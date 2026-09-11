(() => {
  'use strict';

  const CANCELLED_OR_NON_VALUE = new Set(['02', '03', '04', '05']);
  const SUPPORTED_MODELS = new Set(['55', '65']);
  let input = null;

  const brNumber = value => {
    const raw = String(value ?? '').trim();
    if (!raw) return 0;
    const normalized = raw.includes(',') ? raw.replace(/\./g, '').replace(',', '.') : raw;
    const number = Number(normalized);
    return Number.isFinite(number) ? number : 0;
  };

  const money = value => Number(value || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });

  function setStatus(text, kind = 'blue') {
    const el = document.getElementById('statusAuditoria');
    if (!el) return;
    el.replaceChildren();
    const dot = document.createElement('span');
    dot.className = `w-2 h-2 rounded-full ${kind === 'emerald' ? 'bg-emerald-500' : kind === 'red' ? 'bg-red-500' : 'bg-blue-500 animate-pulse'}`;
    el.append(dot, document.createTextNode(` ${text}`));
  }

  function parseC100(line, source) {
    const fields = line.split('|');
    if (fields[1] !== 'C100' || fields.length < 13) return null;

    const indOper = fields[2] || '';
    const codMod = String(fields[5] || '').trim();
    const codSit = String(fields[6] || '').trim().padStart(2, '0');
    if (!SUPPORTED_MODELS.has(codMod)) return null;

    const serie = String(fields[7] || '').trim();
    const numero = String(fields[8] || '').trim();
    const chave = String(fields[9] || '').trim().toUpperCase();
    const data = String(fields[10] || '').trim();
    const valor = CANCELLED_OR_NON_VALUE.has(codSit) ? 0 : brNumber(fields[12]);
    const operacao = indOper === '0' ? 'Entrada' : indOper === '1' ? 'Saída' : 'Não classificada';
    const modelo = codMod === '65' ? 'NFC-e' : 'NF-e';

    return {
      source,
      modelo,
      cod_mod: codMod,
      cod_sit: codSit,
      operacao,
      serie,
      numero,
      chave,
      data,
      valor,
      cancelado: CANCELLED_OR_NON_VALUE.has(codSit)
    };
  }

  function parseSpedText(text, source) {
    const docs = [];
    let has0000 = false;
    let c100Count = 0;

    for (const rawLine of String(text || '').split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line[0] !== '|') continue;
      if (line.startsWith('|0000|')) has0000 = true;
      if (!line.startsWith('|C100|')) continue;
      c100Count += 1;
      const doc = parseC100(line, source);
      if (doc) docs.push(doc);
    }

    if (!has0000) throw new Error(`O arquivo ${source} não parece ser uma EFD ICMS/IPI válida (registro 0000 não encontrado).`);
    return { docs, c100Count };
  }

  function uniqueDocs(docs) {
    const seen = new Map();
    for (const doc of docs) {
      const key = doc.chave || [doc.cod_mod, doc.operacao, doc.serie, doc.numero, doc.data].join('|');
      if (!seen.has(key)) seen.set(key, doc);
    }
    return Array.from(seen.values());
  }

  function summarize(docs) {
    const valid = docs.filter(doc => !doc.cancelado && doc.valor > 0);
    const nfeEntries = valid.filter(doc => doc.cod_mod === '55' && doc.operacao === 'Entrada');
    const nfeOutputs = valid.filter(doc => doc.cod_mod === '55' && doc.operacao === 'Saída');
    const nfceOutputs = valid.filter(doc => doc.cod_mod === '65' && doc.operacao === 'Saída');
    const sum = list => list.reduce((total, doc) => total + doc.valor, 0);

    return {
      sped_nfe_ent: sum(nfeEntries),
      sped_nfe_sai: sum(nfeOutputs),
      sped_nfce_sai: sum(nfceOutputs),
      detalhes: valid.map(doc => ({
        modelo: doc.modelo,
        operacao: doc.operacao,
        numero: doc.numero,
        chave: doc.chave,
        valor: doc.valor,
        serie: doc.serie,
        data: doc.data,
        cod_sit: doc.cod_sit,
        arquivo: doc.source
      }))
    };
  }

  function xmlNfeOutputForConfront() {
    const notes = Array.isArray(xmlNotasGlobais) ? xmlNotasGlobais : [];
    let total = 0;
    let varejo = 0;
    let quantidadeVarejo = 0;
    for (const nota of notes) {
      if (!String(nota?.tipo || '').includes('NF-e')) continue;
      if (String(nota?.tipo || '').includes('NFC-e')) continue;
      if (String(nota?.operacao || '') !== 'Saída') continue;
      if (String(nota?.status || '').includes('Cancelado')) continue;
      const valor = Number(nota?.valor || 0);
      if (valor <= 0) continue;
      if (window.__omnixmlRetailOrigin?.isRetail?.(nota?.chave)) {
        varejo += valor;
        quantidadeVarejo += 1;
      } else {
        total += valor;
      }
    }
    return { total, varejo, quantidadeVarejo };
  }

  function renderComparison(summary) {
    const xmlNfeSai = xmlNfeOutputForConfront();
    const difEnt = Number(xmlNFeApuradoEnt || 0) - summary.sped_nfe_ent;
    const difSai = Number(xmlNfeSai.total || 0) - summary.sped_nfe_sai;
    const difNfce = Number(xmlNFCeApuradoSai || 0) - summary.sped_nfce_sai;

    const values = {
      'mod-xml-nfe-ent': xmlNFeApuradoEnt,
      'mod-sped-nfe-ent': summary.sped_nfe_ent,
      'mod-dif-nfe-ent': difEnt,
      'mod-xml-nfe-sai': xmlNfeSai.total,
      'mod-sped-nfe-sai': summary.sped_nfe_sai,
      'mod-dif-nfe-sai': difSai,
      'mod-xml-nfce-sai': xmlNFCeApuradoSai,
      'mod-sped-nfce-sai': summary.sped_nfce_sai,
      'mod-dif-nfce-sai': difNfce
    };

    for (const [id, value] of Object.entries(values)) {
      const el = document.getElementById(id);
      if (el) el.textContent = money(value);
    }

    for (const [id, value] of [
      ['mod-dif-nfe-ent', difEnt],
      ['mod-dif-nfe-sai', difSai],
      ['mod-dif-nfce-sai', difNfce]
    ]) {
      const el = document.getElementById(id);
      if (!el) continue;
      el.classList.remove('text-emerald-600', 'text-red-600');
      el.classList.add(Math.abs(value) < 0.005 ? 'text-emerald-600' : 'text-red-600');
    }

    document.getElementById('placeholder-sped')?.classList.add('hidden');
    document.getElementById('resultado-sped')?.classList.remove('hidden');
    document.getElementById('btnDivergencias')?.classList.remove('hidden');
    return xmlNfeSai;
  }

  async function processFiles(fileList) {
    const files = Array.from(fileList || []).filter(file => /\.txt$/i.test(file.name));
    if (!files.length) return;
    if (!Array.isArray(xmlNotasGlobais) || xmlNotasGlobais.length === 0) {
      alert('Importe e audite os XMLs antes de processar o SPED Fiscal.');
      return;
    }

    setStatus(`Lendo ${files.length} arquivo(s) SPED localmente...`);
    const docs = [];
    let rawC100 = 0;

    try {
      for (const file of files) {
        const parsed = parseSpedText(await file.text(), file.name);
        docs.push(...parsed.docs);
        rawC100 += parsed.c100Count;
      }

      if (rawC100 === 0) throw new Error('Nenhum registro C100 foi encontrado nos arquivos selecionados.');
      const unique = uniqueDocs(docs);
      const summary = summarize(unique);
      spedNotasDetalhadas = summary.detalhes;
      const xmlNfeSai = renderComparison(summary);
      const fileLabel = files.length === 1 ? '1 arquivo carregado' : `${files.length} arquivos carregados`;
      setStatus(`SPED processado com sucesso · ${fileLabel}`, 'emerald');
      window.__omnixmlSpedLocalLast = {
        files: files.map(file => file.name),
        c100_total: rawC100,
        documentos_suportados: unique.length,
        totais: {
          nfe_entrada: summary.sped_nfe_ent,
          nfe_saida: summary.sped_nfe_sai,
          nfce_saida: summary.sped_nfce_sai,
          nfe_saida_xml_confrontada: xmlNfeSai.total,
          nfe_saida_varejo_excluida: xmlNfeSai.varejo,
          qtd_nfe_varejo_excluida: xmlNfeSai.quantidadeVarejo
        }
      };
    } catch (error) {
      console.error(error);
      setStatus('Falha ao processar o SPED Fiscal', 'red');
      alert(error?.message || 'Falha ao processar o arquivo SPED Fiscal.');
    } finally {
      if (input) input.value = '';
    }
  }

  function install() {
    input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt,text/plain';
    input.multiple = true;
    input.className = 'hidden';
    input.id = 'omnixml-sped-local-input-v26';
    input.addEventListener('change', event => processFiles(event.target.files));
    document.body.appendChild(input);

    window.confrontarSPED = () => input.click();
    window.__omnixmlSpedLocal = {
      version: 28,
      parseSpedText,
      summarize,
      xmlNfeOutputForConfront
    };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
