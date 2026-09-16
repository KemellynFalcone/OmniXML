(() => {
  'use strict';

  const money = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  function getTable(selector) {
    if (!window.jQuery || !jQuery.fn?.dataTable?.isDataTable(selector)) return null;
    return jQuery(selector).DataTable();
  }

  function cancelledNfceBySeries() {
    const table = getTable('#tabelaCancelados');
    if (!table) return [];
    const map = new Map();
    table.rows().data().toArray().forEach(row => {
      const tipo = String(row?.tipo || '');
      if (!tipo.includes('NFC-e')) return;
      const serie = String(row?.serie ?? '').trim() || '—';
      if (!map.has(serie)) map.set(serie, { serie, quantidade: 0, valor: 0 });
      const item = map.get(serie);
      item.quantidade += 1;
      item.valor += Number(row?.valor || 0);
    });
    return Array.from(map.values()).sort((a, b) => {
      const na = Number(a.serie), nb = Number(b.serie);
      if (Number.isFinite(na) && Number.isFinite(nb)) return na - nb;
      return String(a.serie).localeCompare(String(b.serie), 'pt-BR');
    });
  }

  function render() {
    const host = document.getElementById('tab-serie');
    const serieTable = getTable('#tabelaSerie');
    const canceladosTable = getTable('#tabelaCancelados');
    if (!host || !serieTable || !canceladosTable) return false;

    const items = cancelledNfceBySeries();
    let panel = document.getElementById('serie-cancelados-v41');
    if (!panel) {
      panel = document.createElement('section');
      panel.id = 'serie-cancelados-v41';
      panel.className = 'serie-cancelados-v41';
      const wrapper = host.querySelector('#tabelaSerie_wrapper') || host.querySelector('#tabelaSerie');
      if (wrapper) host.insertBefore(panel, wrapper);
      else host.append(panel);
    }

    if (!items.length) {
      panel.innerHTML = `
        <div class="serie-cancelados-v41__head">
          <div>
            <span class="serie-cancelados-v41__eyebrow">Cancelamentos por série</span>
            <strong>Nenhum cupom NFC-e cancelado</strong>
            <small>Não há cancelamentos para somar nas séries processadas.</small>
          </div>
          <span class="serie-cancelados-v41__ok">0 cancelados</span>
        </div>`;
      return true;
    }

    const totalQtd = items.reduce((sum, item) => sum + item.quantidade, 0);
    const totalValor = items.reduce((sum, item) => sum + item.valor, 0);
    const rows = items.map(item => `
      <tr>
        <td><strong>${item.serie}</strong></td>
        <td>${item.quantidade}</td>
        <td class="serie-cancelados-v41__money">${money(item.valor)}</td>
      </tr>`).join('');

    panel.innerHTML = `
      <div class="serie-cancelados-v41__head">
        <div>
          <span class="serie-cancelados-v41__eyebrow">Cancelamentos por série</span>
          <strong>Cupons NFC-e cancelados</strong>
          <small>Soma dos cupons cancelados identificados nos XMLs, agrupados pela série fiscal.</small>
        </div>
        <div class="serie-cancelados-v41__totals">
          <span><b>${totalQtd}</b> cupom${totalQtd === 1 ? '' : 's'}</span>
          <span><b>${money(totalValor)}</b> cancelado</span>
        </div>
      </div>
      <div class="serie-cancelados-v41__table-wrap">
        <table class="serie-cancelados-v41__table">
          <thead><tr><th>Série</th><th>Cupons cancelados</th><th>Valor cancelado</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
    return true;
  }

  function install() {
    let attempts = 0;
    const tryRender = () => {
      attempts += 1;
      if (render() || attempts >= 30) return;
      setTimeout(tryRender, 250);
    };
    tryRender();

    if (window.jQuery) {
      jQuery(document).on('draw.dt.omnixmlSerieCancelados', '#tabelaCancelados, #tabelaSerie', () => render());
    }

    window.OmniXMLSerieCanceladosV41 = { render, cancelledNfceBySeries };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
