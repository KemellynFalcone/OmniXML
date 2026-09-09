(() => {
  'use strict';

  const nativeBlobText = Blob.prototype.text;
  const previousFileText = File.prototype.text;
  const metadata = new Map();

  const fileKey = file => String(file?.webkitRelativePath || file?.name || 'arquivo.xml');
  const basename = value => String(value || '').split(/[\\/]/).pop();
  const localName = node => node ? (node.localName || node.nodeName || '') : '';
  const first = (root, name) => {
    if (!root) return null;
    const ns = root.getElementsByTagNameNS ? root.getElementsByTagNameNS('*', name) : [];
    if (ns && ns.length) return ns[0];
    for (const node of root.getElementsByTagName('*')) if (localName(node) === name) return node;
    return null;
  };
  const text = node => node && node.textContent != null ? node.textContent.trim() : '';
  const normalizeDoc = value => window.__omnixmlCnpj?.normalizar(value) || String(value || '').trim().toUpperCase();
  const normalizeInt = value => {
    const n = Number.parseInt(String(value ?? '').replace(/\D/g, ''), 10);
    return Number.isFinite(n) ? n : null;
  };

  function captureMeta(xml, arquivo) {
    try {
      const doc = new DOMParser().parseFromString(xml, 'application/xml');
      if (doc.querySelector('parsererror')) return;
      const inf = first(doc, 'infNFe');
      if (!inf) return;
      const ide = first(inf, 'ide');
      const emit = first(inf, 'emit');
      const chave = (inf.getAttribute('Id') || '').replace(/^NFe/, '');
      const meta = {
        arquivo,
        numero: normalizeInt(text(first(ide, 'nNF'))),
        serie: normalizeInt(text(first(ide, 'serie'))),
        modelo: text(first(ide, 'mod')),
        chave,
        emitenteCnpj: normalizeDoc(text(first(emit, 'CNPJ')))
      };
      metadata.set(arquivo, meta);
      metadata.set(basename(arquivo), meta);
    } catch (_) {}
  }

  File.prototype.text = async function(...args) {
    const arquivo = fileKey(this);
    const rawPromise = /\.xml$/i.test(arquivo)
      ? nativeBlobText.call(this).catch(() => '')
      : Promise.resolve('');
    try {
      const result = await previousFileText.apply(this, args);
      const raw = await rawPromise;
      if (raw) captureMeta(raw, arquivo);
      return result;
    } catch (error) {
      const raw = await rawPromise;
      if (raw) captureMeta(raw, arquivo);
      throw error;
    }
  };

  function metaFor(row) {
    const key = String(row?.caminho || row?.arquivo || '');
    return metadata.get(key) || metadata.get(basename(key)) || null;
  }

  function failureCanBeJustified(row) {
    const reason = String(row?.motivo || '');
    return /sem protocolo|nfeProc|protNFe|sem autoriza[cç][aã]o v[aá]lida/i.test(reason);
  }

  function matchingInutilizacao(meta, empresaCnpj) {
    if (!meta || meta.numero == null || meta.serie == null || !meta.modelo) return null;
    const company = normalizeDoc(empresaCnpj);
    const issuer = normalizeDoc(meta.emitenteCnpj);
    return (window.__omnixmlInutilizacoes || []).find(item => {
      if (!item?.homologada) return false;
      const inutCnpj = normalizeDoc(item.cnpj);
      if (company && issuer && issuer !== company) return false;
      if (company && inutCnpj && inutCnpj !== company) return false;
      if (issuer && inutCnpj && issuer !== inutCnpj) return false;
      if (String(item.modelo || '') !== String(meta.modelo || '')) return false;
      if (normalizeInt(item.serie) !== meta.serie) return false;
      const ini = normalizeInt(item.inicial);
      const fim = normalizeInt(item.final);
      return ini != null && fim != null && meta.numero >= ini && meta.numero <= fim;
    }) || null;
  }

  function reconcile(dados) {
    const original = Array.isArray(dados?.erros) ? dados.erros : [];
    if (!original.length) return { erros: original, reconciliadas: [] };
    const empresaCnpj = dados?.empresa?.cnpj || '';
    const reconciliadas = [];
    const erros = original.filter(row => {
      if (!failureCanBeJustified(row)) return true;
      const meta = metaFor(row);
      const inut = matchingInutilizacao(meta, empresaCnpj);
      if (!inut) return true;
      reconciliadas.push({
        arquivo: row?.arquivo || row?.caminho || '',
        numero: meta?.numero,
        serie: meta?.serie,
        modelo: meta?.modelo,
        chave: meta?.chave || '',
        protocolo: inut.protocolo || '',
        faixa: `${inut.inicial}-${inut.final}`
      });
      return false;
    });
    return { erros, reconciliadas };
  }

  function syncErrorTable(rows) {
    if (typeof window.dtErros === 'undefined' || !window.dtErros) return;
    try {
      window.dtErros.clear().rows.add(rows).draw();
    } catch (_) {}
  }

  function installDashboardReconciliation() {
    const original = window.atualizarPainelDinamico;
    if (typeof original !== 'function' || original.__omnixmlInutV27) return false;

    const wrapped = function(dados) {
      const result = reconcile(dados || {});
      if (dados && result.reconciliadas.length) {
        dados.erros = result.erros;
        dados.total_erros = result.erros.length;
        dados.inutilizacoes_reconciliadas = result.reconciliadas;
        syncErrorTable(result.erros);
      }
      const retorno = original.apply(this, arguments);
      if (result.reconciliadas.length) {
        const top = document.getElementById('resumo-erros');
        if (top) top.textContent = String(result.erros.length);
        window.__omnixmlFailureReconciliationV27.last = result;
      }
      return retorno;
    };
    wrapped.__omnixmlInutV27 = true;
    window.atualizarPainelDinamico = wrapped;
    return true;
  }

  function ensureLayoutCss() {
    if (document.querySelector('link[data-omnixml-failure-layout-v27]')) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/failure_reconciliation_v27.css?v=1';
    link.dataset.omnixmlFailureLayoutV27 = '1';
    document.head.appendChild(link);
  }

  function start() {
    ensureLayoutCss();
    if (!installDashboardReconciliation()) {
      let attempts = 0;
      const timer = setInterval(() => {
        attempts += 1;
        if (installDashboardReconciliation() || attempts >= 30) clearInterval(timer);
      }, 100);
    }
  }

  window.__omnixmlFailureReconciliationV27 = {
    metadata,
    reconcile,
    last: { erros: [], reconciliadas: [] }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
