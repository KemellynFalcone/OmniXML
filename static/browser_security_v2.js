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

  function configureDataTablesStyleBudget() {
    const dataTable = window.jQuery?.fn?.dataTable;
    if (!dataTable?.defaults) return false;
    dataTable.defaults.autoWidth = false;
    return true;
  }

  function patchRowsAdd(table) {
    if (!table || !table.rows || typeof table.rows.add !== 'function' || table.__omnixmlSafeRowsAdd) return;
    const original = table.rows.add;
    table.rows.add = function(rows) {
      return original.call(this, cloneForDisplay(rows));
    };
    table.__omnixmlSafeRowsAdd = true;
  }

  function patchDataTables() {
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

  const BUCKETS = ['dataTables', 'chartjs', 'app', 'other'];
  const emptyCounters = () => Object.fromEntries(BUCKETS.map(bucket => [bucket, {}]));
  const styleAttrInventory = {
    dataTables: 0,
    chartjs: 0,
    app: 0,
    other: 0,
    properties: emptyCounters(),
    elements: emptyCounters(),
    samples: [],
  };

  function classifyStyledElement(element) {
    if (!(element instanceof Element)) return 'other';
    if (element.tagName === 'CANVAS' || element.closest('canvas')) return 'chartjs';
    if (element.closest('.dataTables_wrapper') || element.matches('table.dataTable, table.dataTable *')) return 'dataTables';
    if (element.closest('#progressContainer, #progressBar')) return 'app';
    return 'other';
  }

  function increment(counter, key) {
    if (!key) return;
    counter[key] = (counter[key] || 0) + 1;
  }

  function elementSignature(element) {
    const tag = element.tagName.toLowerCase();
    if (element.id) return `${tag}#${element.id}`;
    const classes = typeof element.className === 'string'
      ? element.className.trim().split(/\s+/).filter(Boolean).slice(0, 3)
      : [];
    return classes.length ? `${tag}.${classes.join('.')}` : tag;
  }

  function recordStyleProperties(element, bucket) {
    const style = element.style;
    if (!style) return;
    for (let index = 0; index < style.length; index += 1) {
      increment(styleAttrInventory.properties[bucket], style.item(index));
    }
    increment(styleAttrInventory.elements[bucket], elementSignature(element));
  }

  function recordStyleAttribute(element) {
    if (!(element instanceof Element) || !element.hasAttribute('style')) return;
    const bucket = classifyStyledElement(element);
    styleAttrInventory[bucket] += 1;
    recordStyleProperties(element, bucket);
    if (styleAttrInventory.samples.length < 40) {
      styleAttrInventory.samples.push({
        bucket,
        tag: element.tagName.toLowerCase(),
        id: element.id || '',
        className: typeof element.className === 'string' ? element.className.slice(0, 120) : '',
        style: (element.getAttribute('style') || '').slice(0, 200),
      });
    }
  }

  function scanExistingStyleAttributes(root = document) {
    if (!root || typeof root.querySelectorAll !== 'function') return styleAttrInventory;
    root.querySelectorAll('[style]').forEach(recordStyleAttribute);
    return styleAttrInventory;
  }

  function sortedCounter(counter) {
    return Object.fromEntries(Object.entries(counter).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])));
  }

  function styleAttrSnapshot() {
    return {
      counts: Object.fromEntries(BUCKETS.map(bucket => [bucket, styleAttrInventory[bucket]])),
      properties: Object.fromEntries(BUCKETS.map(bucket => [bucket, sortedCounter(styleAttrInventory.properties[bucket])])),
      elements: Object.fromEntries(BUCKETS.map(bucket => [bucket, sortedCounter(styleAttrInventory.elements[bucket])])),
      samples: styleAttrInventory.samples.slice(),
    };
  }

  function resetStyleAttrInventory() {
    for (const bucket of BUCKETS) styleAttrInventory[bucket] = 0;
    styleAttrInventory.properties = emptyCounters();
    styleAttrInventory.elements = emptyCounters();
    styleAttrInventory.samples.length = 0;
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

  configureDataTablesStyleBudget();

  styleAttrInventory.snapshot = styleAttrSnapshot;
  styleAttrInventory.reset = resetStyleAttrInventory;
  window.__omnixmlStyleAttrInventory = styleAttrInventory;
  window.__omnixmlSecurityV2 = {
    limits: LIMITS,
    escapeHtml,
    cloneForDisplay,
    validateSelection,
    configureDataTablesStyleBudget,
    patchDataTables,
    classifyStyledElement,
    scanExistingStyleAttributes,
    styleAttrSnapshot,
    resetStyleAttrInventory,
    styleAttrInventory,
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
