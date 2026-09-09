(() => {
  'use strict';

  const originalText = File.prototype.text;
  const RETAIL_CFOPS = new Set(['5929', '6929']);
  const byKey = new Map();

  const localName = node => node ? (node.localName || node.nodeName || '') : '';
  const first = (root, name) => {
    if (!root) return null;
    const ns = root.getElementsByTagNameNS ? root.getElementsByTagNameNS('*', name) : [];
    if (ns && ns.length) return ns[0];
    for (const node of root.getElementsByTagName('*')) if (localName(node) === name) return node;
    return null;
  };
  const all = (root, name) => {
    if (!root) return [];
    const ns = root.getElementsByTagNameNS ? root.getElementsByTagNameNS('*', name) : [];
    if (ns && ns.length) return Array.from(ns);
    return Array.from(root.getElementsByTagName('*')).filter(node => localName(node) === name);
  };
  const text = node => node?.textContent ? node.textContent.trim() : '';

  function inspect(xml, file) {
    try {
      const doc = new DOMParser().parseFromString(xml, 'application/xml');
      if (doc.querySelector('parsererror')) return;
      const root = doc.documentElement;
      if (!['NFe', 'nfeProc'].includes(localName(root))) return;
      const inf = first(root, 'infNFe');
      if (!inf) return;
      const ide = first(inf, 'ide');
      if (text(first(ide, 'mod')) !== '55') return;
      const chave = (inf.getAttribute('Id') || '').replace(/^NFe/, '').toUpperCase();
      if (!chave) return;
      const cfops = new Set();
      for (const det of all(inf, 'det')) {
        const prod = first(det, 'prod');
        const cfop = text(first(prod, 'CFOP'));
        if (cfop) cfops.add(cfop);
      }
      byKey.set(chave, {
        chave,
        retail: Array.from(cfops).some(cfop => RETAIL_CFOPS.has(cfop)),
        cfops: Array.from(cfops),
        arquivo: file?.webkitRelativePath || file?.name || ''
      });
    } catch (_) {}
  }

  File.prototype.text = async function(...args) {
    const xml = await originalText.apply(this, args);
    inspect(xml, this);
    return xml;
  };

  window.__omnixmlRetailOrigin = {
    version: 28,
    isRetail: chave => Boolean(byKey.get(String(chave || '').toUpperCase())?.retail),
    get: chave => byKey.get(String(chave || '').toUpperCase()) || null,
    snapshot: () => Array.from(byKey.values()).map(item => ({ ...item }))
  };
})();
