(() => {
  const originalText = File.prototype.text;

  function localName(node) {
    return node ? (node.localName || node.nodeName || '') : '';
  }

  function first(root, name) {
    if (!root) return null;
    const ns = root.getElementsByTagNameNS ? root.getElementsByTagNameNS('*', name) : [];
    if (ns && ns.length) return ns[0];
    for (const node of root.getElementsByTagName('*')) {
      if (localName(node) === name) return node;
    }
    return null;
  }

  function text(node) {
    return node && node.textContent ? node.textContent.trim() : '';
  }

  function fiscalError(message) {
    const err = new Error(message);
    err.name = 'OmniXMLFiscalValidationError';
    return err;
  }

  function validateFiscalXml(xml, filename) {
    const doc = new DOMParser().parseFromString(xml, 'application/xml');
    if (doc.querySelector('parsererror')) return;

    const root = doc.documentElement;
    const rootName = localName(root);
    if (!['NFe', 'nfeProc'].includes(rootName)) return;

    const infNFe = first(root, 'infNFe');
    if (!infNFe) throw fiscalError(`${filename}: NF-e/NFC-e sem infNFe.`);

    const ide = first(infNFe, 'ide');
    const modelo = text(first(ide, 'mod'));
    const tpEmis = text(first(ide, 'tpEmis'));
    const numero = text(first(ide, 'nNF')) || filename;

    // Para auditoria fiscal, um XML final deve conter o processo autorizado (nfeProc + protNFe).
    if (rootName === 'NFe') {
      if (tpEmis === '9') {
        throw fiscalError(`${filename}: NFC-e ${numero} emitida em contingência (tpEmis=9), mas o arquivo não contém o protocolo de autorização da SEFAZ (nfeProc/protNFe). Verifique se houve posterior autorização/transmissão.`);
      }
      throw fiscalError(`${filename}: NF-e/NFC-e ${numero} sem protocolo de autorização da SEFAZ. Foi encontrado apenas o XML da NFe, sem nfeProc/protNFe.`);
    }

    const prot = first(root, 'protNFe');
    const infProt = first(prot, 'infProt');
    if (!infProt) throw fiscalError(`${filename}: nfeProc sem bloco protNFe/infProt.`);

    const cStat = text(first(infProt, 'cStat'));
    const xMotivo = text(first(infProt, 'xMotivo'));
    if (!['100', '150'].includes(cStat)) {
      throw fiscalError(`${filename}: documento sem autorização válida da SEFAZ (cStat ${cStat || 'ausente'}${xMotivo ? ` - ${xMotivo}` : ''}).`);
    }

    const assinatura = first(root, 'Signature');
    if (!assinatura) throw fiscalError(`${filename}: documento autorizado sem assinatura digital XML (Signature).`);

    const id = (infNFe.getAttribute('Id') || '').replace(/^NFe/, '');
    const chProt = text(first(infProt, 'chNFe'));
    if (id && chProt && id !== chProt) {
      throw fiscalError(`${filename}: chave do infNFe difere da chave registrada no protocolo SEFAZ.`);
    }

    if (modelo === '65') {
      const qrCode = first(root, 'qrCode');
      if (!qrCode || !text(qrCode)) {
        throw fiscalError(`${filename}: NFC-e autorizada sem QR Code.`);
      }
    }
  }

  File.prototype.text = async function(...args) {
    const xml = await originalText.apply(this, args);
    validateFiscalXml(xml, this.webkitRelativePath || this.name || 'arquivo.xml');
    return xml;
  };
})();
