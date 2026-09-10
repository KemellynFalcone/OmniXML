(() => {
  'use strict';

  const money = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const pct = value => `${Number(value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })}%`;
  const closeMoney = value => Math.abs(Number(value || 0)) < 0.005;
  const closeBase = value => Math.abs(Number(value || 0)) < 0.01;
  const closeRate = value => Math.abs(Number(value || 0)) < 0.0005;

  const effectiveRate = (value, base) => Number(base || 0) ? (Number(value || 0) / Number(base || 0)) * 100 : 0;

  function classify(group) {
    const baseDiff = group.xmlBase - group.efdBase;
    const rateDiff = group.xmlRate - group.efdRate;
    if (closeMoney(group.diff)) return 'Conciliado';
    if (!closeBase(baseDiff) && !closeRate(rateDiff)) return 'Base e alíquota efetiva divergem';
    if (!closeBase(baseDiff)) return 'Base de cálculo divergente';
    if (!closeRate(rateDiff)) return 'Alíquota efetiva divergente';
    return 'Valor divergente com base/alíquota próximas — revisar arredondamento ou escrituração';
  }

  function buildDiagnostic(xml, efdRows) {
    const groups = new Map();
    const ensure = (cst, cfop) => {
      const key = `${cst || '00'}|${cfop || 'N/A'}`;
      if (!groups.has(key)) groups.set(key, {
        key, cst: cst || '00', cfop: cfop || 'N/A', xmlBase: 0, efdBase: 0,
        xmlValue: 0, efdValue: 0, xmlRows: [], efdRows: []
      });
      return groups.get(key);
    };

    for (const row of xml?.cofins_detalhes || []) {
      const group = ensure(row.cst_cofins, row.cfop);
      group.xmlBase += Number(row.base_cofins || 0);
      group.xmlValue += Number(row.valor_cofins || 0);
      group.xmlRows.push(row);
    }
    for (const row of efdRows || []) {
      const group = ensure(row.cst_cofins, row.cfop);
      group.efdBase += Number(row.base_cofins || 0);
      group.efdValue += Number(row.valor_cofins || 0);
      group.efdRows.push(row);
    }

    return Array.from(groups.values()).map(group => {
      group.xmlRate = effectiveRate(group.xmlValue, group.xmlBase);
      group.efdRate = effectiveRate(group.efdValue, group.efdBase);
      group.diff = group.xmlValue - group.efdValue;
      group.cause = classify(group);
      return group;
    }).filter(group => !closeMoney(group.diff))
      .sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff) || a.cfop.localeCompare(b.cfop));
  }

  function uniqueCount(rows, key) {
    const values = rows.map(row => row?.[key]).filter(Boolean);
    return values.length ? new Set(values).size : rows.length;
  }

  function traceSummary(group) {
    return `${uniqueCount(group.xmlRows, 'chave')} XMLs × ${group.efdRows.length} registros EFD`;
  }

  function noteNumber(row) {
    const explicit = row.numero || row.nNF || row.num_doc || row.numero_documento;
    if (explicit) return String(explicit);
    const key = String(row.chave || '');
    if (key.length >= 34) {
      const value = key.slice(25, 34).replace(/^0+/, '');
      if (value) return value;
    }
    return '—';
  }

  function td(text, className = '') {
    const cell = document.createElement('td');
    cell.textContent = text;
    if (className) cell.className = className;
    return cell;
  }

  function th(text) {
    const cell = document.createElement('th');
    cell.textContent = text;
    return cell;
  }

  function detailsTable(rows, origin) {
    const wrap = document.createElement('div');
    wrap.className = 'cofins-auditor-v35__detail-wrap';
    const title = document.createElement('h6');
    title.textContent = origin === 'XML' ? `XMLs envolvidos (${rows.length})` : `Registros EFD envolvidos (${rows.length})`;
    wrap.append(title);

    const tableWrap = document.createElement('div');
    tableWrap.className = 'cofins-auditor-v35__detail-scroll';
    const table = document.createElement('table');
    table.className = 'cofins-auditor-v35__detail-table';
    const head = document.createElement('thead');
    const hr = document.createElement('tr');
    ['Nota','Chave','CFOP','CST','Base COFINS','COFINS','Referência'].forEach(label => hr.append(th(label)));
    head.append(hr);
    const body = document.createElement('tbody');

    for (const row of rows) {
      const tr = document.createElement('tr');
      const reference = origin === 'EFD'
        ? `${row.source || 'EFD'}${row.line ? `:L${row.line}` : ''}`
        : 'XML';
      tr.append(
        td(noteNumber(row)),
        td(row.chave || '—', 'cofins-auditor-v35__key'),
        td(row.cfop || '—'),
        td(row.cst_cofins || '—'),
        td(money(row.base_cofins)),
        td(money(row.valor_cofins)),
        td(reference, 'cofins-auditor-v35__reference')
      );
      body.append(tr);
    }
    table.append(head, body);
    tableWrap.append(table);
    wrap.append(tableWrap);
    return wrap;
  }

  function closeDetails() {
    document.getElementById('cofins-auditor-v35-modal')?.remove();
  }

  function openDetails(group) {
    closeDetails();
    const modal = document.createElement('div');
    modal.id = 'cofins-auditor-v35-modal';
    modal.className = 'cofins-auditor-v35__modal';
    const dialog = document.createElement('div');
    dialog.className = 'cofins-auditor-v35__dialog';
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');

    const header = document.createElement('div');
    header.className = 'cofins-auditor-v35__header';
    const heading = document.createElement('div');
    const title = document.createElement('h5');
    title.textContent = `Detalhes COFINS — CST ${group.cst} / CFOP ${group.cfop}`;
    const subtitle = document.createElement('p');
    subtitle.textContent = `${traceSummary(group)} • diferença ${money(group.diff)}. Arquivo/linha é referência técnica para localizar o registro no SPED.`;
    heading.append(title, subtitle);
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'cofins-auditor-v35__close';
    close.dataset.cofinsClose = '1';
    close.setAttribute('aria-label', 'Fechar detalhes');
    close.textContent = '×';
    header.append(heading, close);

    const content = document.createElement('div');
    content.className = 'cofins-auditor-v35__content';
    content.append(detailsTable(group.xmlRows, 'XML'), detailsTable(group.efdRows, 'EFD'));
    dialog.append(header, content);
    modal.append(dialog);
    document.body.append(modal);
  }

  function traceCell(group, index) {
    const cell = document.createElement('td');
    cell.className = 'cofins-auditor-v34__trace';
    const summary = document.createElement('div');
    summary.className = 'cofins-auditor-v35__summary';
    summary.textContent = traceSummary(group);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'cofins-auditor-v35__details-btn';
    button.dataset.cofinsDetails = String(index);
    button.textContent = 'Ver detalhes';
    cell.append(summary, button);
    return cell;
  }

  function render() {
    const section = document.getElementById('pis-cofins-confront-v30');
    if (!section) return false;
    document.getElementById('cofins-auditor-v34')?.remove();
    closeDetails();

    const xml = window.__omnixmlXmlPisCofins?.snapshot?.();
    const efd = window.__omnixmlEfdContribLast;
    if (!xml?.cofins_detalhes || !efd?.detalhes) return false;

    const diagnostic = buildDiagnostic(xml, efd.detalhes);
    const block = document.createElement('div');
    block.id = 'cofins-auditor-v34';
    block.className = 'cofins-auditor-v34';

    const title = document.createElement('h5');
    title.textContent = 'Auditor de cálculo COFINS';
    const intro = document.createElement('p');
    intro.textContent = diagnostic.length
      ? 'Compara base de cálculo e alíquota efetiva por CST/CFOP para explicar a diferença documental. A causa indicada é diagnóstica e deve ser validada antes de qualquer ajuste fiscal.'
      : 'COFINS conciliada por CST/CFOP dentro da tolerância.';
    block.append(title, intro);

    if (diagnostic.length) {
      const wrap = document.createElement('div');
      wrap.className = 'cofins-auditor-v34__wrap';
      const table = document.createElement('table');
      table.className = 'cofins-auditor-v34__table';
      const thead = document.createElement('thead');
      const hr = document.createElement('tr');
      ['CST','CFOP','Base XML','Base EFD','Alíq. efetiva XML','Alíq. efetiva EFD','COFINS XML','COFINS EFD','Diferença','Diagnóstico','Rastreabilidade'].forEach(label => hr.append(th(label)));
      thead.append(hr);
      const tbody = document.createElement('tbody');
      diagnostic.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.append(
          td(item.cst), td(item.cfop), td(money(item.xmlBase)), td(money(item.efdBase)),
          td(pct(item.xmlRate)), td(pct(item.efdRate)), td(money(item.xmlValue)), td(money(item.efdValue)),
          td(money(item.diff), 'cofins-auditor-v34__diff'), td(item.cause, 'cofins-auditor-v34__cause'),
          traceCell(item, index)
        );
        tbody.append(tr);
      });
      table.append(thead, tbody); wrap.append(table); block.append(wrap);
    }

    section.append(block);
    window.__omnixmlCofinsAuditorV34 = { version: 35, buildDiagnostic, groups: diagnostic, last: diagnostic.map(item => ({
      cst_cofins: item.cst, cfop: item.cfop, base_xml: item.xmlBase, base_efd: item.efdBase,
      aliquota_efetiva_xml: item.xmlRate, aliquota_efetiva_efd: item.efdRate,
      cofins_xml: item.xmlValue, cofins_efd: item.efdValue, diferenca: item.diff, diagnostico: item.cause,
      rastreabilidade: traceSummary(item)
    })) };
    return true;
  }

  function install() {
    const observerOptions = { childList: true, subtree: true };
    let refreshing = false;
    const observer = new MutationObserver(() => {
      // A abertura do drill-down também altera o DOM. Enquanto o modal existir,
      // essa mutação é da própria UI do auditor e não deve disparar novo render.
      if (document.getElementById('cofins-auditor-v35-modal')) return;
      if (!window.__omnixmlEfdContribLast || refreshing) return;
      refreshing = true;
      observer.disconnect();
      try {
        render();
      } finally {
        observer.observe(document.body, observerOptions);
        refreshing = false;
      }
    });

    document.addEventListener('click', event => {
      const detailsButton = event.target.closest('[data-cofins-details]');
      if (detailsButton) {
        const index = Number(detailsButton.dataset.cofinsDetails);
        const group = window.__omnixmlCofinsAuditorV34?.groups?.[index];
        if (group) openDetails(group);
        return;
      }
      if (event.target.closest('[data-cofins-close]') || event.target.id === 'cofins-auditor-v35-modal') closeDetails();
    });

    render();
    observer.observe(document.body, observerOptions);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
