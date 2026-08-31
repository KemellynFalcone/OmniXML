(() => {
  const originalText = File.prototype.text;
  const store = new Map();
  window.__omnixmlInutilizacoes = [];

  const localName = node => node ? (node.localName || node.nodeName || '') : '';
  const text = node => node && node.textContent != null ? node.textContent.trim() : '';
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
  const childText = (root, name) => text(first(root, name));

  function publicar() {
    window.__omnixmlInutilizacoes = Array.from(store.values());
  }

  function resetar() {
    store.clear();
    publicar();
  }

  // Limpa a conciliação antes de uma nova seleção de arquivos/pasta.
  document.addEventListener('change', event => {
    const id = event.target && event.target.id;
    if (id === 'omnixml-local-input-arquivos' || id === 'omnixml-local-input-pasta') resetar();
  }, true);

  function parseInutilizacao(xml, arquivo) {
    const doc = new DOMParser().parseFromString(xml, 'application/xml');
    if (doc.querySelector('parsererror')) return null;
    const root = doc.documentElement;
    const nome = localName(root);
    if (!['procInutNFe', 'retInutNFe', 'inutNFe'].includes(nome)) return null;

    const blocos = all(root, 'infInut');
    if (!blocos.length) return null;
    const resposta = blocos.find(inf => childText(inf, 'cStat')) || null;
    const origem = resposta || blocos[0];
    const fallback = blocos[0];
    const valor = campo => childText(origem, campo) || childText(fallback, campo);
    const cStat = resposta ? childText(resposta, 'cStat') : '';
    const nNFIni = Number.parseInt(valor('nNFIni'), 10);
    const nNFFin = Number.parseInt(valor('nNFFin'), 10);
    if (!Number.isFinite(nNFIni) || !Number.isFinite(nNFFin)) return null;

    return {
      tipo: 'inutilizacao',
      arquivo,
      cstat: cStat,
      homologada: cStat === '102',
      motivo: resposta ? childText(resposta, 'xMotivo') : 'Pedido de inutilização sem retorno homologado no arquivo.',
      cnpj: valor('CNPJ'),
      modelo: valor('mod'),
      serie: valor('serie'),
      inicial: Math.min(nNFIni, nNFFin),
      final: Math.max(nNFIni, nNFFin),
      protocolo: resposta ? childText(resposta, 'nProt') : '',
      justificativa: childText(fallback, 'xJust')
    };
  }

  function registrar(item) {
    const chave = [item.cnpj, item.modelo, item.serie, item.inicial, item.final, item.protocolo || item.arquivo].join('|');
    store.set(chave, item);
    publicar();
  }

  // O processador legado ainda não conhece procInutNFe/retInutNFe. Depois de capturar
  // os dados, entregamos um evento vazio para que o arquivo não seja marcado como erro.
  const eventoNeutro = '<evento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"></evento>';

  File.prototype.text = async function(...args) {
    const xml = await originalText.apply(this, args);
    const arquivo = this.webkitRelativePath || this.name || 'arquivo.xml';
    const inutilizacao = parseInutilizacao(xml, arquivo);
    if (!inutilizacao) return xml;
    registrar(inutilizacao);
    return eventoNeutro;
  };
})();
