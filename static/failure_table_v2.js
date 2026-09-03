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
  const escapeHtml = value => String(value ?? '').replace(/[&<>\"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', "'": '&#39;'
  }[c]));
  const brl = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const basename = value => String(value || '').split(/[\\/]/).pop();
  const node = (tag, className = '', text = '') => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== '') el.textContent = String(text);
    return el;
  };

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

  function summaryCard(label, id, boxClass, labelClass, valueClass, initial) {
    const box = node('div', `rounded-xl border p-4 ${boxClass}`);
    box.appendChild(node('div', `text-xs font-bold uppercase tracking-wider ${labelClass}`, label));
    const value = node('div', `text-2xl font-black mt-1 ${valueClass}`, initial);
    value.id = id;
    box.appendChild(value);
    return box;
  }

  function ensureSummary() {
    const table = document.getElementById('tabelaErros');
    if (!table) return null;
    document.getElementById('omnixml-falhas-financeiras')?.remove();
    document.getElementById('omnixml-total-arquivos-falha')?.remove();
    let summary = document.getElementById('omnixml-failure-summary-v2');
    if (!summary) {
      summary = node('div', 'grid grid-cols-1 md:grid-cols-3 gap-4 mb-5');
      summary.id = 'omnixml-failure-summary-v2';
      summary.append(
        summaryCard('XMLs com falha', 'failure-v2-count', 'border-rose-200 bg-rose-50', 'text-rose-500', 'text-rose-700', '0'),
        summaryCard('Valor total envolvido', 'failure-v2-value', 'border-amber-200 bg-amber-50', 'text-amber-600', 'text-amber-700', 'R$ 0,00'),
        summaryCard('Chaves identificadas', 'failure-v2-keys', 'border-blue-200 bg-blue-50', 'text-blue-600', 'text-blue-700', '0')
      );
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
    let total = 0, keys = 0;
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

  function rebuildHeader(table) {
    table.replaceChildren();
    const thead = node('thead', 'bg-slate-50');
    const row = node('tr');
    for (const label of ['Arquivo', 'Nº Cupom/Nota', 'Chave de Acesso', 'Valor (R$)', 'Motivo']) row.appendChild(node('th', '', label));
    thead.appendChild(row);
    table.append(thead, node('tbody'));
  }

  function rebuildTable() {
    if (typeof $ === 'undefined' || typeof $.fn?.DataTable === 'undefined') return false;
    const table = document.getElementById('tabelaErros');
    if (!table || typeof dtErros === 'undefined' || !dtErros) return false;
    if (table.dataset.failureV2 === '1') return true;

    const settings = dtErros.settings?.()[0];
    if (settings && settings._bInitComplete === false) return false;

    let current = [];
    try { current = dtErros.rows().data().toArray(); } catch (_) {}
    try { dtErros.destroy(); } catch (_) { return false; }

    table.dataset.failureV2 = '1';
    rebuildHeader(table);

    dtErros = $('#tabelaErros').DataTable({
      language: { url: '/static/datatables_ptbr_v10.json' },
      responsive: false,
      autoWidth: false,
      pageLength: 25,
      deferRender: true,
      dom: '<"flex justify-between items-center mb-4"Bf>rt<"flex justify-between items-center mt-4"ip>',
      buttons: [{ extend: 'excelHtml5', text: 'Exportar Excel', className: 'dt-button' }],
      data: current,
      columns: [
        { data: 'arquivo', width: '16%', className: 'font-mono font-semibold text-slate-700', render: (d, type, row) => { const value = basename(row?.arquivo || row?.caminho || d || ''); return type === 'display' ? escapeHtml(value) : value; } },
        { data: null, width: '9%', className: 'font-mono font-bold text-slate-800 whitespace-nowrap', render: (d, type, row) => { const value = metaFor(row).numero || '—'; return type === 'display' ? escapeHtml(value) : value; } },
        { data: null, width: '34%', className: 'font-mono text-xs text-slate-600 break-all', render: (d, type, row) => { const value = metaFor(row).chave || 'Não identificada'; return type === 'display' ? escapeHtml(value) : value; }, createdCell: (cell, d, row) => { const chave = metaFor(row).chave || ''; cell.title = chave; if (!chave) cell.classList.add('text-slate-400', 'italic'); } },
        { data: null, width: '12%', className: 'font-bold text-slate-800 whitespace-nowrap text-right', render: (d, type, row) => type === 'display' ? brl(metaFor(row).valor || 0) : Number(metaFor(row).valor || 0) },
        { data: 'motivo', width: '29%', render: (reason, type) => type !== 'display' ? String(reason || '') : escapeHtml(`⚠️ ${shortReason(reason)}`), createdCell: (cell, reason) => { cell.title = String(reason || ''); cell.classList.add('truncate', 'px-2', 'py-1', 'rounded', 'bg-rose-50', 'text-rose-700', 'border', 'border-rose-200', 'font-medium', 'text-xs', 'cursor-help'); } }
      ],
      order: [[1, 'asc']]
    });

    ensureSummary();
    $('#tabelaErros').off('draw.failureV2').on('draw.dt.failureV2', updateSummary);
    updateSummary();
    return true;
  }

  function start() {
    if (typeof $ === 'undefined' || typeof $.fn?.DataTable === 'undefined') {
      setTimeout(start, 100);
      return;
    }
    const $table = $('#tabelaErros');
    if (!$table.length) return;

    let done = false;
    const rebuildOnce = () => {
      if (done) return;
      if (rebuildTable()) done = true;
      else setTimeout(rebuildOnce, 100);
    };

    $table.one('init.dt.failureV2Bootstrap', (_event, settings) => {
      if (settings?.nTable?.id === 'tabelaErros') setTimeout(rebuildOnce, 0);
    });

    if ($.fn.DataTable.isDataTable('#tabelaErros')) {
      const settings = dtErros?.settings?.()[0];
      if (settings?._bInitComplete) setTimeout(rebuildOnce, 0);
    }
  }

  start();
})();
