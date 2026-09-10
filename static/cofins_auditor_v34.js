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
        cst: cst || '00', cfop: cfop || 'N/A', xmlBase: 0, efdBase: 0,
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

  function trace(group) {
    const keys = Array.from(new Set(group.xmlRows.map(row => row.chave).filter(Boolean)));
    const refs = Array.from(new Set(group.efdRows.map(row => `${row.source}:L${row.line}`)));
    const xmlText = keys.length ? `${keys.length} chave(s): ${keys.slice(0, 2).map(key => key.slice(-10)).join(', ')}${keys.length > 2 ? '…' : ''}` : '—';
    const efdText = refs.length ? `${refs.length} linha(s): ${refs.slice(0, 2).join(', ')}${refs.length > 2 ? '…' : ''}` : '—';
    return `XML ${xmlText} | EFD ${efdText}`;
  }

  function td(text, className = '') {
    const cell = document.createElement('td');
    cell.textContent = text;
    if (className) cell.className = className;
    return cell;
  }

  function render() {
    const section = document.getElementById('pis-cofins-confront-v30');
    if (!section) return false;
    document.getElementById('cofins-auditor-v34')?.remove();

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
      ['CST','CFOP','Base XML','Base EFD','Alíq. efetiva XML','Alíq. efetiva EFD','COFINS XML','COFINS EFD','Diferença','Diagnóstico','Rastreabilidade'].forEach(label => {
        const th = document.createElement('th'); th.textContent = label; hr.append(th);
      });
      thead.append(hr);
      const tbody = document.createElement('tbody');
      for (const item of diagnostic) {
        const tr = document.createElement('tr');
        tr.append(
          td(item.cst), td(item.cfop), td(money(item.xmlBase)), td(money(item.efdBase)),
          td(pct(item.xmlRate)), td(pct(item.efdRate)), td(money(item.xmlValue)), td(money(item.efdValue)),
          td(money(item.diff), 'cofins-auditor-v34__diff'), td(item.cause, 'cofins-auditor-v34__cause'),
          td(trace(item), 'cofins-auditor-v34__trace')
        );
        tbody.append(tr);
      }
      table.append(thead, tbody); wrap.append(table); block.append(wrap);
    }

    section.append(block);
    window.__omnixmlCofinsAuditorV34 = { version: 34, buildDiagnostic, last: diagnostic.map(item => ({
      cst_cofins: item.cst, cfop: item.cfop, base_xml: item.xmlBase, base_efd: item.efdBase,
      aliquota_efetiva_xml: item.xmlRate, aliquota_efetiva_efd: item.efdRate,
      cofins_xml: item.xmlValue, cofins_efd: item.efdValue, diferenca: item.diff, diagnostico: item.cause
    })) };
    return true;
  }

  function install() {
    const observer = new MutationObserver(() => { if (window.__omnixmlEfdContribLast) render(); });
    observer.observe(document.body, { childList: true, subtree: true });
    render();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
