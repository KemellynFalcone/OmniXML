(() => {
  const LIMITS = Object.freeze({
    maxFiles: 50000,
    maxFileBytes: 20 * 1024 * 1024,
    maxTotalBytes: 1536 * 1024 * 1024,
  });

  const INPUT_IDS = new Set([
    'omnixml-local-input-arquivos',
    'omnixml-local-input-pasta',
  ]);

  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));

  function cloneForDisplay(value) {
    if (Array.isArray(value)) return value.map(cloneForDisplay);
    if (!value || typeof value !== 'object') {
      return typeof value === 'string' ? escapeHtml(value) : value;
    }
    const clone = {};
    for (const [key, item] of Object.entries(value)) clone[key] = cloneForDisplay(item);
    return clone;
  }

  function validateSelection(files) {
    const list = Array.from(files || []);
    if (list.length > LIMITS.maxFiles) {
      return `A seleção contém ${list.length.toLocaleString('pt-BR')} arquivos. O limite de segurança é ${LIMITS.maxFiles.toLocaleString('pt-BR')}.`;
    }

    let total = 0;
    for (const file of list) {
      if (!/\.xml$/i.test(file.name || '')) continue;
      const size = Number(file.size || 0);
      total += size;
      if (size > LIMITS.maxFileBytes) {
        const mb = (size / 1024 / 1024).toLocaleString('pt-BR', { maximumFractionDigits: 1 });
        return `O XML “${file.name || 'arquivo.xml'}” possui ${mb} MB e excede o limite individual de 20 MB.`;
      }
      if (total > LIMITS.maxTotalBytes) {
        return 'A seleção de XMLs excede 1,5 GB. Divida a auditoria em lotes menores para evitar esgotamento de memória do navegador.';
      }
    }
    return '';
  }

  document.addEventListener('change', event => {
    const input = event.target;
    if (!input || !INPUT_IDS.has(input.id)) return;
    const failure = validateSelection(input.files);
    if (!failure) return;

    event.preventDefault();
    event.stopImmediatePropagation();
    try { input.value = ''; } catch (_) {}
    window.alert(`OmniXML bloqueou esta seleção por segurança.\n\n${failure}`);
  }, true);

  function patchRowsAdd(table) {
    if (!table || !table.rows || typeof table.rows.add !== 'function' || table.__omnixmlSafeRowsAdd) return;
    const original = table.rows.add;
    table.rows.add = function(rows) {
      return original.call(this, cloneForDisplay(rows));
    };
    table.__omnixmlSafeRowsAdd = true;
  }

  function patchDataTables() {
    // As tabelas abaixo recebem dados derivados de XML/SPED. Sanitizamos uma cópia
    // exclusivamente para renderização, preservando os dados fiscais de origem.
    const tables = [];
    try {
      if (typeof dtNFe !== 'undefined') tables.push(dtNFe);
      if (typeof dtNFCe !== 'undefined') tables.push(dtNFCe);
      if (typeof dtCancelados !== 'undefined') tables.push(dtCancelados);
      if (typeof dtCFOP !== 'undefined') tables.push(dtCFOP);
      if (typeof dtCST !== 'undefined') tables.push(dtCST);
      if (typeof dtSerie !== 'undefined') tables.push(dtSerie);
      if (typeof dtAuditoria !== 'undefined') tables.push(dtAuditoria);
      if (typeof dtProdutos !== 'undefined') tables.push(dtProdutos);
      if (typeof dtDivergencias !== 'undefined') tables.push(dtDivergencias);
      if (typeof dtPisCofins !== 'undefined') tables.push(dtPisCofins);
      if (typeof dtErros !== 'undefined') tables.push(dtErros);
    } catch (_) {}
    tables.forEach(patchRowsAdd);
    return tables.length > 0;
  }

  const styleAttrInventory = {
    dataTables: 0,
    chartjs: 0,
    app: 0,
    other: 0,
    samples: [],
  };

  function classifyStyledElement(element) {
    if (!(element instanceof Element)) return 'other';
    if (element.tagName === 'CANVAS' || element.closest('canvas')) return 'chartjs';
    if (element.closest('.dataTables_wrapper') || element.matches('table.dataTable, table.dataTable *')) return 'dataTables';
    if (element.closest('#progressContainer, #progressBar')) return 'app';
    return 'other';
  }

  function recordStyleAttribute(element) {
    if (!(element instanceof Element) || !element.hasAttribute('style')) return;
    const bucket = classifyStyledElement(element);
    styleAttrInventory[bucket] += 1;
    if (styleAttrInventory.samples.length < 25) {
      styleAttrInventory.samples.push({
        bucket,
        tag: element.tagName.toLowerCase(),
        id: element.id || '',
        className: typeof element.className === 'string' ? element.className.slice(0, 120) : '',
        style: (element.getAttribute('style') || '').slice(0, 160),
      });
    }
  }

  function scanExistingStyleAttributes(root = document) {
    if (!root || typeof root.querySelectorAll !== 'function') return styleAttrInventory;
    root.querySelectorAll('[style]').forEach(recordStyleAttribute);
    return styleAttrInventory;
  }

  function startStyleAttrInventory() {
    scanExistingStyleAttributes();
    const observer = new MutationObserver(mutations => {
      for (const mutation of mutations) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
          recordStyleAttribute(mutation.target);
          continue;
        }
        for (const node of mutation.addedNodes || []) {
          if (!(node instanceof Element)) continue;
          if (node.hasAttribute('style')) recordStyleAttribute(node);
          node.querySelectorAll?.('[style]').forEach(recordStyleAttribute);
        }
      }
    });
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['style'],
    });
    return observer;
  }

  function start() {
    let attempts = 0;
    const timer = setInterval(() => {
      const ready = patchDataTables();
      if (ready || ++attempts > 80) clearInterval(timer);
    }, 100);
    startStyleAttrInventory();
  }

  window.__omnixmlStyleAttrInventory = styleAttrInventory;
  window.__omnixmlSecurityV2 = {
    limits: LIMITS,
    escapeHtml,
    cloneForDisplay,
    validateSelection,
    patchDataTables,
    classifyStyledElement,
    scanExistingStyleAttributes,
    styleAttrInventory,
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
