(() => {
  'use strict';

  const previousText = File.prototype.text;
  const notes = new Map();
  const cancelled = new Set();

  const localName = node => node ? (node.localName || node.nodeName || '') : '';
  const text = node => node?.textContent ? node.textContent.trim() : '';
  const num = value => {
    const parsed = Number(String(value ?? '').replace(',', '.'));
    return Number.isFinite(parsed) ? parsed : 0;
  };
  const all = (root, name) => {
    if (!root) return [];
    const ns = root.getElementsByTagNameNS ? root.getElementsByTagNameNS('*', name) : [];
    if (ns?.length) return Array.from(ns);
    return Array.from(root.getElementsByTagName('*')).filter(node => localName(node) === name);
  };
  const first = (root, name) => all(root, name)[0] || null;
  const docId = root => text(first(root, 'CNPJ')) || text(first(root, 'CPF')) || '';

  function taxGroup(det, taxName) {
    const tax = first(det, taxName);
    if (!tax) return { cst: '', base: 0, value: 0 };
    const group = Array.from(tax.children || [])[0] || tax;
    return {
      cst: text(first(group, 'CST')).padStart(2, '0'),
      base: num(text(first(group, 'vBC'))),
      value: num(text(first(group, taxName === 'PIS' ? 'vPIS' : 'vCOFINS')))
    };
  }

  function inspectEvent(root) {
    const event = all(root, 'infEvento').find(node => text(first(node, 'tpEvento')) === '110111');
    if (!event) return;
    const key = text(first(event, 'chNFe')).toUpperCase();
    const statuses = all(root, 'cStat').map(text);
    if (key && statuses.some(status => ['135', '155'].includes(status))) cancelled.add(key);
  }

  function inspectNFe(root, file) {
    const inf = first(root, 'infNFe');
    if (!inf) return;
    const ide = first(inf, 'ide');
    const model = text(first(ide, 'mod'));
    if (!['55', '65'].includes(model)) return;
    const id = inf.getAttribute('Id') || '';
    const key = id.replace(/^NFe/, '').toUpperCase();
    if (!key) return;
    const emit = first(inf, 'emit');
    const dest = first(inf, 'dest');
    const items = [];

    for (const det of all(inf, 'det')) {
      const prod = first(det, 'prod');
      if (!prod) continue;
      const pis = taxGroup(det, 'PIS');
      const cofins = taxGroup(det, 'COFINS');
      const gross = num(text(first(prod, 'vProd')));
      const discount = num(text(first(prod, 'vDesc')));
      items.push({
        cfop: text(first(prod, 'CFOP')),
        receita: Math.max(0, gross - discount),
        cst_pis: pis.cst,
        base_pis: pis.base,
        valor_pis: pis.value,
        cst_cofins: cofins.cst,
        base_cofins: cofins.base,
        valor_cofins: cofins.value
      });
    }

    notes.set(key, {
      chave: key,
      modelo: model,
      emitente_cnpj: docId(emit),
      destinatario_cnpj: docId(dest),
      arquivo: file?.webkitRelativePath || file?.name || '',
      itens: items
    });
  }

  function inspect(xml, file) {
    try {
      const doc = new DOMParser().parseFromString(xml, 'application/xml');
      if (doc.querySelector('parsererror')) return;
      const root = doc.documentElement;
      const rootName = localName(root);
      if (['evento', 'procEventoNFe', 'retEvento'].includes(rootName)) inspectEvent(root);
      if (['NFe', 'nfeProc'].includes(rootName)) inspectNFe(root, file);
    } catch (_) {}
  }

  function identifyCompany() {
    const counts = new Map();
    const add = note => {
      if (!note.emitente_cnpj) return;
      counts.set(note.emitente_cnpj, (counts.get(note.emitente_cnpj) || 0) + 1);
    };
    const values = Array.from(notes.values());
    values.filter(note => note.modelo === '65').forEach(add);
    if (!counts.size) values.forEach(add);
    let company = '';
    let max = -1;
    for (const [cnpj, count] of counts) {
      if (count > max) { company = cnpj; max = count; }
    }
    return company;
  }

  function snapshot() {
    const company = identifyCompany();
    const byCst = new Map();
    let outputs = 0;

    for (const note of notes.values()) {
      if (!company || note.emitente_cnpj !== company || cancelled.has(note.chave)) continue;
      outputs += 1;
      for (const item of note.itens) {
        const cst = item.cst_pis || '00';
        const current = byCst.get(cst) || {
          cst,
          vl_opr: 0,
          vl_pis: 0,
          vl_cofins: 0,
          vl_bc_pis: 0,
          vl_bc_cofins: 0,
          itens: 0
        };
        current.vl_opr += item.receita;
        current.vl_pis += item.valor_pis;
        current.vl_cofins += item.valor_cofins;
        current.vl_bc_pis += item.base_pis;
        current.vl_bc_cofins += item.base_cofins;
        current.itens += 1;
        byCst.set(cst, current);
      }
    }

    const csts = Array.from(byCst.values()).sort((a, b) => b.vl_opr - a.vl_opr || a.cst.localeCompare(b.cst));
    return {
      version: 30,
      empresa_cnpj: company,
      notas_saida: outputs,
      canceladas_identificadas: cancelled.size,
      totais: {
        receita: csts.reduce((sum, row) => sum + row.vl_opr, 0),
        pis: csts.reduce((sum, row) => sum + row.vl_pis, 0),
        cofins: csts.reduce((sum, row) => sum + row.vl_cofins, 0)
      },
      csts
    };
  }

  File.prototype.text = async function(...args) {
    const value = await previousText.apply(this, args);
    if (/\.xml$/i.test(this.name || '')) inspect(value, this);
    return value;
  };

  window.__omnixmlXmlPisCofins = { version: 30, snapshot };
})();
