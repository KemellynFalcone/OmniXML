(() => {
  'use strict';

  const money = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

  function getTable(selector) {
    if (!window.jQuery || !jQuery.fn?.dataTable?.isDataTable(selector)) return null;
    return jQuery(selector).DataTable();
  }

  function cancelledByTypeAndSeries() {
    const table = getTable('#tabelaCancelados');
    if (!table) return new Map();
    const map = new Map();
    table.rows().data().toArray().forEach(row => {
      const tipo = String(row?.tipo || '').trim() || 'Documento';
      const serie = String(row?.serie ?? '').trim() || '—';
      const key = `${tipo}|${serie}`;
      if (!map.has(key)) map.set(key, { tipo, serie, quantidade: 0, valor: 0 });
      const item = map.get(key);
      item.quantidade += 1;
      item.valor += Number(row?.valor || 0);
    });
    return map;
  }

  function detailForSeries(data) {
    const tipo = String(data?.tipo || '').trim() || 'Documento';
    const serie = String(data?.serie ?? '').trim() || '—';
    const liquido = Number(data?.valor || 0);
    const cancellation = cancelledByTypeAndSeries().get(`${tipo}|${serie}`);
    const cancelado = Number(cancellation?.valor || 0);
    const bruto = liquido + cancelado;
    return { tipo, serie, liquido, cancelado, bruto, quantidade: Number(cancellation?.quantidade || 0) };
  }

  function detailMarkup(data) {
    const detail = detailForSeries(data);
    return `
      <div class="serie-detalhe-v42" role="region" aria-label="Resumo da série ${escapeHtml(detail.serie)}">
        <div class="serie-detalhe-v42__head">
          <div>
            <span class="serie-detalhe-v42__eyebrow">Resumo financeiro da série</span>
            <strong>${escapeHtml(detail.tipo)} · Série ${escapeHtml(detail.serie)}</strong>
          </div>
          <small>${detail.quantidade} documento${detail.quantidade === 1 ? '' : 's'} cancelado${detail.quantidade === 1 ? '' : 's'}</small>
        </div>
        <div class="serie-detalhe-v42__metrics">
          <div class="serie-detalhe-v42__metric serie-detalhe-v42__metric--gross">
            <span>Total bruto</span>
            <strong>${money(detail.bruto)}</strong>
          </div>
          <div class="serie-detalhe-v42__metric serie-detalhe-v42__metric--cancelled">
            <span>Cancelado</span>
            <strong>${money(detail.cancelado)}</strong>
          </div>
          <div class="serie-detalhe-v42__metric serie-detalhe-v42__metric--net">
            <span>Total líquido</span>
            <strong>${money(detail.liquido)}</strong>
          </div>
        </div>
        <p class="serie-detalhe-v42__formula">Total bruto = total líquido + cancelamentos da série.</p>
      </div>`;
  }

  function markRowsClickable() {
    const table = getTable('#tabelaSerie');
    if (!table) return false;
    jQuery('#tabelaSerie tbody tr').each(function() {
      const row = table.row(this);
      if (!row.data()) return;
      this.classList.add('serie-detalhe-v42__trigger');
      this.setAttribute('tabindex', '0');
      this.setAttribute('role', 'button');
      this.setAttribute('aria-expanded', row.child.isShown() ? 'true' : 'false');
      this.setAttribute('title', 'Clique para ver total bruto, cancelado e líquido');
    });
    return true;
  }

  function toggleSeriesDetail(rowNode) {
    const serieTable = getTable('#tabelaSerie');
    if (!serieTable) return;
    const row = serieTable.row(rowNode);
    const data = row.data();
    if (!data) return;

    if (row.child.isShown()) {
      row.child.hide();
      rowNode.classList.remove('serie-detalhe-v42__trigger--open');
      rowNode.setAttribute('aria-expanded', 'false');
      return;
    }

    jQuery('#tabelaSerie tbody tr.serie-detalhe-v42__trigger--open').each(function() {
      const opened = serieTable.row(this);
      if (opened.data() && opened.child.isShown()) opened.child.hide();
      this.classList.remove('serie-detalhe-v42__trigger--open');
      this.setAttribute('aria-expanded', 'false');
    });

    row.child(detailMarkup(data), 'serie-detalhe-v42-row').show();
    rowNode.classList.add('serie-detalhe-v42__trigger--open');
    rowNode.setAttribute('aria-expanded', 'true');
  }

  function install() {
    let attempts = 0;
    const tryBind = () => {
      attempts += 1;
      if (markRowsClickable() || attempts >= 30) return;
      setTimeout(tryBind, 250);
    };
    tryBind();

    if (window.jQuery) {
      jQuery(document).on('draw.dt.omnixmlSerieDetalhe', '#tabelaSerie', () => markRowsClickable());
      jQuery(document)
        .off('click.omnixmlSerieDetalhe', '#tabelaSerie tbody tr')
        .on('click.omnixmlSerieDetalhe', '#tabelaSerie tbody tr', function(event) {
          if (jQuery(event.target).closest('a,button,input,select,textarea').length) return;
          toggleSeriesDetail(this);
        })
        .off('keydown.omnixmlSerieDetalhe', '#tabelaSerie tbody tr')
        .on('keydown.omnixmlSerieDetalhe', '#tabelaSerie tbody tr', function(event) {
          if (event.key !== 'Enter' && event.key !== ' ') return;
          event.preventDefault();
          toggleSeriesDetail(this);
        });
    }

    window.OmniXMLSerieCanceladosV41 = {
      cancelledByTypeAndSeries,
      detailForSeries,
      toggleSeriesDetail,
      markRowsClickable
    };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
