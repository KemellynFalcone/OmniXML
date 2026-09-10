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
      if (!groups.has(key)) groups.set(key, { key, cst: cst || '00', cfop: cfop || 'N/A', xmlBase: 0, efdBase: 0, xmlValue: 0, efdValue: 0, xmlRows: [], efdRows: [] });
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
    }).filter(group => !closeMoney(group.diff)).sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff) || a.cfop.localeCompare(b.cfop));
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

  function aggregateByKey(rows) {
    const map = new Map();
    for (const row of rows || []) {
      const key = String(row.chave || '').trim();
      if (!key) continue;
      if (!map.has(key)) map.set(key, { chave: key, numero: noteNumber(row), cfop: row.cfop || '—', cst_cofins: row.cst_cofins || '—', base_cofins: 0, valor_cofins: 0, source: row.source || '', line: row.line || '', rows: [] });
      const item = map.get(key);
      item.base_cofins += Number(row.base_cofins || 0);
      item.valor_cofins += Number(row.valor_cofins || 0);
      item.rows.push(row);
      if (!item.source && row.source) item.source = row.source;
      if (!item.line && row.line) item.line = row.line;
    }
    return map;
  }

  function buildDivergenceEvidence(group) {
    const xmlWithKey = group.xmlRows.filter(row => String(row.chave || '').trim());
    const efdWithKey = group.efdRows.filter(row => String(row.chave || '').trim());
    const pareamento_seguro = xmlWithKey.length === group.xmlRows.length && efdWithKey.length === group.efdRows.length && xmlWithKey.length > 0 && efdWithKey.length > 0;
    if (!pareamento_seguro) return { pareamento_seguro: false, divergentXmlRows: [], divergentEfdRows: [], conciliadosOcultos: 0, divergentCount: null, note: 'Diferença agregada sem vínculo individual conclusivo. Os registros conciliados não são listados para evitar confusão.' };

    const xmlMap = aggregateByKey(group.xmlRows);
    const efdMap = aggregateByKey(group.efdRows);
    const keys = new Set([...xmlMap.keys(), ...efdMap.keys()]);
    const divergentXmlRows = [];
    const divergentEfdRows = [];
    let conciliadosOcultos = 0;
    for (const key of keys) {
      const xmlRow = xmlMap.get(key);
      const efdRow = efdMap.get(key);
      const xmlValue = Number(xmlRow?.valor_cofins || 0);
      const efdValue = Number(efdRow?.valor_cofins || 0);
      if (xmlRow && efdRow && closeMoney(xmlValue - efdValue)) {
        conciliadosOcultos += 1;
        continue;
      }
      if (xmlRow) divergentXmlRows.push(xmlRow);
      if (efdRow) divergentEfdRows.push(efdRow);
    }
    return {
      pareamento_seguro: true,
      divergentXmlRows,
      divergentEfdRows,
      conciliadosOcultos,
      divergentCount: new Set([...divergentXmlRows.map(row => row.chave), ...divergentEfdRows.map(row => row.chave)]).size,
      note: conciliadosOcultos ? `${conciliadosOcultos} documento(s) conciliado(s) oculto(s).` : 'Nenhum documento conciliado foi incluído no detalhe.'
    };
  }

  function buildActionGuidance(group, evidence) {
    const baseDiff = group.xmlBase - group.efdBase;
    const rateDiff = group.xmlRate - group.efdRate;
    let action = 'Revisar o valor de COFINS escriturado e confrontar os registros divergentes com os XMLs antes de qualquer ajuste fiscal.';
    if (!closeBase(baseDiff) && !closeRate(rateDiff)) action = 'Revisar base de cálculo, CST e alíquota da COFINS na escrituração e nos XMLs; validar a origem da diferença antes de qualquer ajuste fiscal.';
    else if (!closeBase(baseDiff)) action = 'Revisar a composição da base de cálculo da COFINS na EFD e nos XMLs; conferir exclusões, reduções e CST antes de qualquer ajuste fiscal.';
    else if (!closeRate(rateDiff)) action = 'Revisar CST e alíquota da COFINS na escrituração e confrontar com os XMLs; validar antes de qualquer ajuste fiscal.';

    const confidence = evidence.pareamento_seguro && evidence.divergentCount ? 'Alta' : 'Média';
    const evidenceText = evidence.pareamento_seguro
      ? `${evidence.divergentCount} documento(s) divergente(s) identificados por chave no CST ${group.cst} / CFOP ${group.cfop}.`
      : `Diferença agregada no CST ${group.cst} / CFOP ${group.cfop}, sem vínculo individual conclusivo.`;
    return { action, confidence, evidenceText };
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
    title.textContent = origin === 'XML' ? `XMLs divergentes (${rows.length})` : `Registros EFD divergentes (${rows.length})`;
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
      const reference = origin === 'EFD' ? `${row.source || 'EFD'}${row.line ? `:L${row.line}` : ''}` : 'XML';
      tr.append(td(noteNumber(row)), td(row.chave || '—', 'cofins-auditor-v35__key'), td(row.cfop || '—'), td(row.cst_cofins || '—'), td(money(row.base_cofins)), td(money(row.valor_cofins)), td(reference, 'cofins-auditor-v35__reference'));
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

  function guidanceCard(group, evidence) {
    const guidance = buildActionGuidance(group, evidence);
    const card = document.createElement('div');
    card.className = 'cofins-auditor-v37__guidance';
    const rows = [
      ['Diagnóstico', group.cause],
      ['Impacto', money(Math.abs(group.diff))],
      ['Evidência', guidance.evidenceText],
      ['Ação sugerida', guidance.action],
      ['Confiança', guidance.confidence]
    ];
    for (const [label, value] of rows) {
      const item = document.createElement('div');
      item.className = 'cofins-auditor-v37__guidance-row';
      const strong = document.createElement('strong');
      strong.textContent = label;
      const span = document.createElement('span');
      span.textContent = value;
      item.append(strong, span);
      card.append(item);
    }
    const note = document.createElement('p');
    note.textContent = 'Orientação diagnóstica: validar antes de qualquer ajuste fiscal.';
    card.append(note);
    return { card, guidance };
  }

  function openDetails(group) {
    closeDetails();
    const evidence = buildDivergenceEvidence(group);
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
    title.textContent = `Diferença COFINS — CST ${group.cst} / CFOP ${group.cfop}`;
    const subtitle = document.createElement('p');
    subtitle.textContent = evidence.pareamento_seguro ? `${evidence.divergentCount} documento(s) explicam a diferença ${money(group.diff)}. ${evidence.note}` : `${money(group.diff)} de diferença no grupo. ${evidence.note}`;
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
    const guidance = guidanceCard(group, evidence);
    content.append(guidance.card);

    const conclusion = document.createElement('div');
    conclusion.className = 'cofins-auditor-v36__conclusion';
    const conclusionTitle = document.createElement('strong');
    conclusionTitle.textContent = group.cause;
    const conclusionText = document.createElement('span');
    conclusionText.textContent = ` Base XML ${money(group.xmlBase)} × EFD ${money(group.efdBase)}; alíquota efetiva XML ${pct(group.xmlRate)} × EFD ${pct(group.efdRate)}; COFINS XML ${money(group.xmlValue)} × EFD ${money(group.efdValue)}.`;
    conclusion.append(conclusionTitle, conclusionText);
    content.append(conclusion);

    if (evidence.pareamento_seguro) {
      if (evidence.divergentXmlRows.length) content.append(detailsTable(evidence.divergentXmlRows, 'XML'));
      if (evidence.divergentEfdRows.length) content.append(detailsTable(evidence.divergentEfdRows, 'EFD'));
    } else {
      const aggregate = document.createElement('div');
      aggregate.className = 'cofins-auditor-v36__aggregate';
      const aggregateTitle = document.createElement('strong');
      aggregateTitle.textContent = 'Diferença agregada sem vínculo individual conclusivo';
      const aggregateText = document.createElement('p');
      aggregateText.textContent = 'A EFD deste grupo não fornece chave suficiente para relacionar cada linha a uma nota específica com segurança. Por isso o OmniXML não lista todos os XMLs/registros como se fossem divergentes. Use o diagnóstico agregado acima para revisar base, alíquota e valor.';
      aggregate.append(aggregateTitle, aggregateText);
      content.append(aggregate);
    }

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
    intro.textContent = diagnostic.length ? 'Compara base de cálculo e alíquota efetiva por CST/CFOP para explicar a diferença documental. A causa indicada é diagnóstica e deve ser validada antes de qualquer ajuste fiscal.' : 'COFINS conciliada por CST/CFOP dentro da tolerância.';
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
        tr.append(td(item.cst), td(item.cfop), td(money(item.xmlBase)), td(money(item.efdBase)), td(pct(item.xmlRate)), td(pct(item.efdRate)), td(money(item.xmlValue)), td(money(item.efdValue)), td(money(item.diff), 'cofins-auditor-v34__diff'), td(item.cause, 'cofins-auditor-v34__cause'), traceCell(item, index));
        tbody.append(tr);
      });
      table.append(thead, tbody);
      wrap.append(table);
      block.append(wrap);
    }

    section.append(block);
    window.__omnixmlCofinsAuditorV34 = {
      version: 37,
      buildDiagnostic,
      buildDivergenceEvidence,
      buildActionGuidance,
      groups: diagnostic,
      last: diagnostic.map(item => {
        const evidence = buildDivergenceEvidence(item);
        const guidance = buildActionGuidance(item, evidence);
        return {
          cst_cofins: item.cst,
          cfop: item.cfop,
          base_xml: item.xmlBase,
          base_efd: item.efdBase,
          aliquota_efetiva_xml: item.xmlRate,
          aliquota_efetiva_efd: item.efdRate,
          cofins_xml: item.xmlValue,
          cofins_efd: item.efdValue,
          diferenca: item.diff,
          diagnostico: item.cause,
          evidencia: guidance.evidenceText,
          acao_sugerida: guidance.action,
          confianca: guidance.confidence,
          rastreabilidade: traceSummary(item)
        };
      })
    };
    return true;
  }

  function install() {
    const observerOptions = { childList: true, subtree: true };
    let refreshing = false;
    const observer = new MutationObserver(() => {
      if (document.getElementById('cofins-auditor-v35-modal')) return;
      if (!window.__omnixmlEfdContribLast || refreshing) return;
      refreshing = true;
      observer.disconnect();
      try { render(); } finally {
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
