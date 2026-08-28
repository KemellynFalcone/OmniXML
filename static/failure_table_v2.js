(() => {
  const originalText = File.prototype.text;
  const metadata = new Map();

  const fileKey = file => String(file?.webkitRelativePath || file?.name || 'arquivo.xml');
  const localName = node => node ? (node.localName || node.nodeName || '') : '';
  const first = (root, name) => {
    if (!root) return null;
    const ns = root.getElementsByTagNameNS ? root.getElementsByTagNameNS('*', name) : [];
    if (ns && ns.length) return ns[0];
    for (const node of root.getElementsByTagName('*')) if (localName(node) === name) return node;
    return null;
  };
  const txt = node => node && node.textContent ? node.textContent.trim() : '';
  const escapeHtml = value => String(value ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  const brl = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const basename = value => String(value || '').split(/[\\/]/).pop();

  function extractMeta(xml, arquivo) {
    try {
      const doc = new DOMParser().parseFromString(xml, 'application/xml');
      if (doc.querySelector('parsererror')) return;
      const inf = first(doc, 'infNFe');
      if (!inf) return;
      const ide = first(inf, 'ide');
      const total = first(inf, 'ICMSTot');
      const chave = (inf.getAttribute('Id') || '').replace(/^NFe/, '');
      const meta = {
        arquivo,
        numero: txt(first(ide, 'nNF')) || '—',
        serie: txt(first(ide, 'serie')) || '—',
        modelo: txt(first(ide, 'mod')) || '',
        chave: chave || '',
        valor: Number(String(txt(first(total, 'vNF')) || '0').replace(',', '.')) || 0
      };
      metadata.set(arquivo, meta);
      metadata.set(basename(arquivo), meta);
    } catch (_) {}
  }

  File.prototype.text = async function(...args) {
    const xml = await originalText.apply(this, args);
    extractMeta(xml, fileKey(this));
    return xml;
  };

  function metaFor(row) {
    const key = String(row?.caminho || row?.arquivo || '');
    return metadata.get(key) || metadata.get(basename(key)) || {};
  }

  function shortReason(reason) {
    const r = String(reason || 'Falha de validação fiscal.');
    if (/contingência/i.test(r) && /protocolo/i.test(r)) return 'Contingência sem protocolo SEFAZ';
    if (/sem protocolo|nfeProc|protNFe/i.test(r)) return 'Sem protocolo de autorização SEFAZ';
    if (/assinatura/i.test(r)) return 'Assinatura digital ausente';
    if (/cStat/i.test(r)) return 'Status SEFAZ inválido';
    if (/QR Code/i.test(r)) return 'QR Code ausente';
    if (/malformado|inválido/i.test(r)) return 'XML inválido';
    return r.length > 48 ? `${r.slice(0, 45)}...` : r;
  }

  function ensureSummary() {
    const tab = document.getElementById('tab-erros');
    const table = document.getElementById('tabelaErros');
    if (!tab || !table) return null;

    document.getElementById('omnixml-falhas-financeiras')?.remove();
    document.getElementById('omnixml-total-arquivos-falha')?.remove();

    let summary = document.getElementById('omnixml-failure-summary-v2');
    if (!summary) {
      summary = document.createElement('div');
      summary.id = 'omnixml-failure-summary-v2';
      summary.className = 'grid grid-cols-1 md:grid-cols-3 gap-4 mb-5';
      summary.innerHTML = `
        <div class="rounded-xl border border-rose-200 bg-rose-50 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-rose-500">XMLs com falha</div>
          <div id="failure-v2-count" class="text-2xl font-black text-rose-700 mt-1">0</div>
        </div>
        <div class="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-amber-600">Valor total envolvido</div>
          <div id="failure-v2-value" class="text-2xl font-black text-amber-700 mt-1">R$ 0,00</div>
        </div>
        <div class="rounded-xl border border-blue-200 bg-blue-50 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-blue-600">Chaves identificadas</div>
          <div id="failure-v2-keys" class="text-2xl font-black text-blue-700 mt-1">0</div>
        </div>`;
      table.parentElement.insertBefore(summary, table.parentElement.firstChild);
    }
    return summary;
  }

  function updateSummary() {
    if (typeof dtErros === 'undefined' || !dtErros) return;
    const rows = dtErros.rows().data().toArray();
    const unique = new Map();
    for (const row of rows) {
      const key = String(row?.caminho || row?.arquivo || '').toLowerCase();
      if (key && !unique.has(key)) unique.set(key, row);
    }
    let total = 0;
    let keys = 0;
    for (const row of unique.values()) {
      const meta = metaFor(row);
      total += Number(meta.valor || 0);
      if (meta.chave) keys++;
    }
    const c = document.getElementById('failure-v2-count');
    const v = document.getElementById('failure-v2-value');
    const k = document.getElementById('failure-v2-keys');
    if (c) c.textContent = unique.size.toLocaleString('pt-BR');
    if (v) v.textContent = brl(total);
    if (k) k.textContent = keys.toLocaleString('pt-BR');
    const top = document.getElementById('resumo-erros');
    if (top) top.textContent = String(unique.size);
  }

  function rebuildTable() {
    if (typeof $ === 'undefined' || typeof $.fn?.DataTable === 'undefined') return false;
    const table = document.getElementById('tabelaErros');
    if (!table || typeof dtErros === 'undefined' || !dtErros) return false;
    if (table.dataset.failureV2 === '1') return true;

    let current = [];
    try { current = dtErros.rows().data().toArray(); } catch (_) {}
    try { dtErros.destroy(); } catch (_) {}

    table.dataset.failureV2 = '1';
    table.innerHTML = `
      <thead class="bg-slate-50">
        <tr>
          <th>Arquivo</th>
          <th>Nº Cupom/Nota</th>
          <th>Chave de Acesso</th>
          <th>Valor (R$)</th>
          <th>Motivo</th>
        </tr>
      </thead>
      <tbody></tbody>`;

    dtErros = $('#tabelaErros').DataTable({
      language: { url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json' },
      responsive: false,
      autoWidth: false,
      pageLength: 25,
      deferRender: true,
      dom: '<"flex justify-between items-center mb-4"Bf>rt<"flex justify-between items-center mt-4"ip>',
      buttons: [{ extend: 'excelHtml5', text: 'Exportar Excel', className: 'dt-button' }],
      data: current,
      columns: [
        {
          data: 'arquivo',
          width: '16%',
          className: 'font-mono font-semibold text-slate-700',
          render: (d, type, row) => type === 'display' ? escapeHtml(basename(row?.arquivo || row?.caminho || d || '')) : basename(row?.arquivo || row?.caminho || d || '')
        },
        {
          data: null,
          width: '9%',
          className: 'font-mono font-bold text-slate-800 whitespace-nowrap',
          render: (d, type, row) => escapeHtml(metaFor(row).numero || '—')
        },
        {
          data: null,
          width: '34%',
          className: 'font-mono text-xs text-slate-600',
          render: (d, type, row) => {
            const chave = metaFor(row).chave || '';
            if (!chave) return '<span class="text-slate-400 italic">Não identificada</span>';
            return `<span class="break-all" title="${escapeHtml(chave)}">${escapeHtml(chave)}</span>`;
          }
        },
        {
          data: null,
          width: '12%',
          className: 'font-bold text-slate-800 whitespace-nowrap text-right',
          render: (d, type, row) => type === 'display' ? brl(metaFor(row).valor || 0) : Number(metaFor(row).valor || 0)
        },
        {
          data: 'motivo',
          width: '29%',
          render: (reason, type) => {
            if (type !== 'display') return String(reason || '');
            return `<span class="inline-block max-w-full truncate px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium text-xs cursor-help" title="${escapeHtml(reason || '')}">⚠️ ${escapeHtml(shortReason(reason))}</span>`;
          }
        }
      ],
      order: [[1, 'asc']]
    });

    ensureSummary();
    $('#tabelaErros').off('draw.failureV2').on('draw.dt.failureV2', updateSummary);
    updateSummary();
    return true;
  }

  function start() {
    let attempts = 0;
    const timer = setInterval(() => {
      if (rebuildTable() || ++attempts > 80) clearInterval(timer);
    }, 250);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
