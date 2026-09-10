(() => {
  'use strict';

  const previousText = File.prototype.text;
  const xmlRows = new Map();
  const efdRows = new Map();
  const cancelled = new Set();
  const money = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const localName = node => node ? (node.localName || node.nodeName || '') : '';
  const text = node => node?.textContent ? node.textContent.trim() : '';
  const num = value => {
    const raw = String(value ?? '').trim();
    if (!raw) return 0;
    const normalized = raw.includes(',') ? raw.replace(/\./g, '').replace(',', '.') : raw;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
  };
  const all = (root, name) => {
    if (!root) return [];
    const ns = root.getElementsByTagNameNS ? root.getElementsByTagNameNS('*', name) : [];
    if (ns?.length) return Array.from(ns);
    return Array.from(root.getElementsByTagName('*')).filter(node => localName(node) === name);
  };
  const first = (root, name) => all(root, name)[0] || null;

  function competence(value) {
    const raw = String(value || '').trim();
    if (!raw) return 'Competência não identificada';
    const iso = raw.match(/^(\d{4})-(\d{2})/);
    if (iso) return `${iso[2]}/${iso[1]}`;
    const br = raw.match(/^(\d{2})(\d{2})(\d{4})$/);
    if (br) return `${br[2]}/${br[3]}`;
    const slash = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (slash) return `${slash[2]}/${slash[3]}`;
    return 'Competência não identificada';
  }

  function taxGroup(det) {
    const cofins = first(det, 'COFINS');
    if (!cofins) return { cst: '00', base: 0, value: 0 };
    const group = Array.from(cofins.children || [])[0] || cofins;
    return {
      cst: text(first(group, 'CST')).padStart(2, '0') || '00',
      base: num(text(first(group, 'vBC'))),
      value: num(text(first(group, 'vCOFINS')))
    };
  }

  function inspectXml(raw, file) {
    try {
      const doc = new DOMParser().parseFromString(raw, 'application/xml');
      if (doc.querySelector('parsererror')) return;
      const root = doc.documentElement;
      const rootName = localName(root);

      if (['evento', 'procEventoNFe', 'retEvento'].includes(rootName)) {
        const event = all(root, 'infEvento').find(node => text(first(node, 'tpEvento')) === '110111');
        const key = event ? text(first(event, 'chNFe')).toUpperCase() : '';
        const statuses = all(root, 'cStat').map(text);
        if (key && statuses.some(status => ['135', '155'].includes(status))) cancelled.add(key);
        return;
      }

      if (!['NFe', 'nfeProc'].includes(rootName)) return;
      const inf = first(root, 'infNFe');
      if (!inf) return;
      const ide = first(inf, 'ide');
      const model = text(first(ide, 'mod'));
      if (!['55', '65'].includes(model)) return;
      const key = String(inf.getAttribute('Id') || '').replace(/^NFe/, '').toUpperCase();
      if (!key) return;
      const date = text(first(ide, 'dhEmi')) || text(first(ide, 'dEmi'));
      const numero = text(first(ide, 'nNF'));
      const serie = text(first(ide, 'serie'));
      const source = file?.webkitRelativePath || file?.name || 'XML';

      for (const det of all(inf, 'det')) {
        const prod = first(det, 'prod');
        if (!prod) continue;
        const cofins = taxGroup(det);
        const cfop = text(first(prod, 'CFOP')) || 'N/A';
        const item = det.getAttribute('nItem') || '';
        const rowKey = `${key}|${item}|${cfop}|${cofins.cst}`;
        xmlRows.set(rowKey, {
          origem: 'XML', source, chave: key, numero, serie, item,
          data: date, competencia: competence(date), cfop,
          cst_cofins: cofins.cst, base_cofins: cofins.base, valor_cofins: cofins.value
        });
      }
    } catch (_) {}
  }

  function inspectEfd(raw, file) {
    if (!/^\s*\|0000\|/m.test(String(raw || ''))) return;
    const source = file?.webkitRelativePath || file?.name || 'EFD';
    let currentOper = '';
    let current = {};
    let lineNumber = 0;

    for (const rawLine of String(raw || '').split(/\r?\n/)) {
      lineNumber += 1;
      const line = rawLine.trim();
      if (!line.startsWith('|')) continue;
      const fields = line.split('|');
      const reg = fields[1] || '';

      if (reg === 'C100') {
        currentOper = String(fields[2] || '').trim();
        current = {
          numero: String(fields[8] || '').trim(),
          chave: String(fields[9] || '').trim().toUpperCase(),
          data: String(fields[11] || fields[10] || '').trim()
        };
        continue;
      }
      if (currentOper !== '1') continue;

      let row = null;
      if (reg === 'C170') {
        const cst = String(fields[31] || '').trim().padStart(2, '0');
        if (!cst || cst === '00') continue;
        row = {
          cfop: String(fields[11] || '').trim() || 'N/A',
          cst_cofins: cst,
          base_cofins: num(fields[32]),
          valor_cofins: num(fields[36])
        };
      } else if (reg === 'C175') {
        const cst = String(fields[11] || '').trim().padStart(2, '0');
        if (!cst || cst === '00') continue;
        row = {
          cfop: String(fields[2] || '').trim() || 'N/A',
          cst_cofins: cst,
          base_cofins: num(fields[12]),
          valor_cofins: num(fields[16])
        };
      }
      if (!row) continue;

      const key = `${source}|${lineNumber}|${reg}`;
      efdRows.set(key, {
        origem: 'EFD', source, line: lineNumber, registro: reg,
        chave: current.chave || '', numero: current.numero || '', data: current.data || '',
        competencia: competence(current.data), ...row
      });
    }
  }

  File.prototype.text = async function(...args) {
    const value = await previousText.apply(this, args);
    const name = String(this.name || '');
    if (/\.xml$/i.test(name)) inspectXml(value, this);
    else if (/\.txt$/i.test(name)) inspectEfd(value, this);
    return value;
  };

  function modalFilter(modal) {
    const title = modal?.querySelector('.cofins-auditor-v35__header h5')?.textContent || '';
    return {
      cst: title.match(/CST\s+([^\s/]+)/i)?.[1] || '',
      cfop: title.match(/CFOP\s+([^\s]+)/i)?.[1] || ''
    };
  }

  function aggregateDocuments(rows) {
    const docs = new Map();
    for (const row of rows) {
      const docKey = row.chave || `${row.origem}|${row.source}|${row.numero || 'S/N'}`;
      if (!docs.has(docKey)) docs.set(docKey, {
        chave: row.chave || '', numero: row.numero || '—', competencia: row.competencia,
        xml: 0, efd: 0, xmlBase: 0, efdBase: 0, refs: []
      });
      const doc = docs.get(docKey);
      if (row.origem === 'XML') {
        doc.xml += Number(row.valor_cofins || 0);
        doc.xmlBase += Number(row.base_cofins || 0);
      } else {
        doc.efd += Number(row.valor_cofins || 0);
        doc.efdBase += Number(row.base_cofins || 0);
        doc.refs.push(`${row.source}:L${row.line}`);
      }
    }
    return Array.from(docs.values()).map(doc => ({ ...doc, diff: doc.xml - doc.efd }));
  }

  function matchingRows(cst, cfop) {
    const xml = Array.from(xmlRows.values()).filter(row => !cancelled.has(row.chave) && row.cst_cofins === cst && row.cfop === cfop);
    const efd = Array.from(efdRows.values()).filter(row => row.cst_cofins === cst && row.cfop === cfop);
    return [...xml, ...efd];
  }

  function el(tag, className, textValue) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (textValue !== undefined) node.textContent = textValue;
    return node;
  }

  function cell(textValue, className = '') {
    const td = el('td', className, textValue);
    td.style.padding = '9px 10px';
    td.style.borderBottom = '1px solid #f1f5f9';
    return td;
  }

  function renderDocuments(container, rows, competenceName) {
    container.replaceChildren();
    const docs = aggregateDocuments(rows).sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));
    const safe = docs.length > 0 && docs.every(doc => doc.chave);

    const note = el('div', '', safe
      ? 'Pareamento por chave disponível: os documentos abaixo podem ser confrontados individualmente.'
      : 'Diferença agregada — parte dos registros não possui chave suficiente para vínculo nota a nota.');
    note.style.cssText = `margin-bottom:10px;padding:9px 10px;border-radius:8px;font-size:12px;${safe ? 'background:#ecfdf5;color:#166534' : 'background:#fffbeb;color:#92400e'}`;
    container.append(note);

    const wrap = el('div');
    wrap.style.overflow = 'auto';
    const table = el('table');
    table.style.cssText = 'width:100%;border-collapse:collapse;min-width:760px;font-size:12px';
    const thead = el('thead');
    const hr = el('tr');
    ['Documento', 'Chave', 'COFINS XML', 'COFINS EFD', 'Diferença', 'Referência EFD'].forEach(label => {
      const th = el('th', '', label);
      th.style.cssText = 'padding:8px 10px;text-align:left;color:#64748b;font-size:10px;text-transform:uppercase;border-bottom:1px solid #e2e8f0';
      hr.append(th);
    });
    thead.append(hr);
    const tbody = el('tbody');
    for (const doc of docs) {
      const tr = el('tr');
      const keyText = doc.chave ? `${doc.chave.slice(0, 8)}…${doc.chave.slice(-8)}` : 'Sem chave conclusiva';
      tr.append(
        cell(doc.numero),
        cell(keyText),
        cell(money(doc.xml)),
        cell(money(doc.efd)),
        cell(money(doc.diff)),
        cell(doc.refs.join(', ') || 'XML')
      );
      tbody.append(tr);
    }
    table.append(thead, tbody);
    wrap.append(table);
    container.append(wrap);

    if (!docs.length) {
      container.append(el('p', '', `Nenhum documento localizado para ${competenceName}.`));
    }
  }

  function renderNavigation(modal) {
    if (!modal || modal.querySelector('#cofins-origem-v39')) return;
    const content = modal.querySelector('.cofins-auditor-v35__content');
    if (!content) return;
    const { cst, cfop } = modalFilter(modal);
    if (!cst || !cfop) return;

    const rows = matchingRows(cst, cfop);
    const competencies = new Map();
    for (const row of rows) {
      const key = row.competencia || 'Competência não identificada';
      if (!competencies.has(key)) competencies.set(key, []);
      competencies.get(key).push(row);
    }

    const panel = el('section');
    panel.id = 'cofins-origem-v39';
    panel.style.cssText = 'margin:14px 0;padding:14px;border:1px solid #c7d2fe;border-radius:12px;background:#fff';
    const eyebrow = el('div', '', 'v39 · Origem da diferença');
    eyebrow.style.cssText = 'font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#4f46e5';
    panel.append(eyebrow);
    const title = el('strong', '', 'Competência → CST → CFOP → Documento');
    title.style.cssText = 'display:block;margin-top:3px;color:#0f172a';
    panel.append(title);
    const subtitle = el('p', '', `CST ${cst} / CFOP ${cfop}: selecione a competência para chegar aos documentos que compõem a diferença.`);
    subtitle.style.cssText = 'font-size:12px;color:#64748b;margin:4px 0 12px';
    panel.append(subtitle);

    const selectorWrap = el('div');
    selectorWrap.style.cssText = 'display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px';
    const select = el('select');
    select.id = 'cofins-v39-competencia';
    select.style.cssText = 'border:1px solid #cbd5e1;border-radius:8px;padding:8px 10px;background:#fff;color:#0f172a;font-size:12px';
    const sorted = Array.from(competencies.keys()).sort((a, b) => b.localeCompare(a));
    if (!sorted.length) sorted.push('Competência não identificada');
    for (const item of sorted) {
      const option = el('option', '', item);
      option.value = item;
      select.append(option);
    }
    const breadcrumb = el('span', '', `CST ${cst} › CFOP ${cfop}`);
    breadcrumb.style.cssText = 'font-size:12px;font-weight:700;color:#475569';
    selectorWrap.append(select, breadcrumb);
    panel.append(selectorWrap);

    const detail = el('div');
    detail.id = 'cofins-v39-documentos';
    panel.append(detail);

    const refresh = () => renderDocuments(detail, competencies.get(select.value) || [], select.value);
    select.addEventListener('change', refresh);
    refresh();

    const treatment = content.querySelector('#cofins-tratativa-v38');
    if (treatment?.nextSibling) content.insertBefore(panel, treatment.nextSibling);
    else content.insertBefore(panel, content.children[2] || null);
  }

  const observer = new MutationObserver(() => {
    const modal = document.getElementById('cofins-auditor-v35-modal');
    if (modal) renderNavigation(modal);
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });

  window.OmniXMLCofinsOrigemV39 = {
    competence,
    matchingRows,
    aggregateDocuments,
    snapshot: () => ({ xml: Array.from(xmlRows.values()), efd: Array.from(efdRows.values()) })
  };
})();
