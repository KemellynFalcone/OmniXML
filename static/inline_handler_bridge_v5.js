(() => {
  'use strict';

  const ALLOWED = new Set([
    'fecharModalProduto',
    'mudarAba',
    'iniciarProcessamento',
    'filtrarPeloCard',
    'filtrarCancelados',
    'filtrarInconsistencias',
    'filtrarErros',
    'toggleSidebar',
    'limparESairCliente',
    'exportarRelatorioGeral',
    'importarPisCofins',
    'confrontarSPED',
    'mostrarDivergencias',
    'abrirModalProduto',
    'copiarEAbrir'
  ]);

  const splitArgs = raw => {
    const args = [];
    let current = '';
    let quote = '';
    let escaped = false;
    for (const ch of raw) {
      if (escaped) {
        current += ch;
        escaped = false;
        continue;
      }
      if (ch === '\\') {
        current += ch;
        escaped = true;
        continue;
      }
      if (quote) {
        current += ch;
        if (ch === quote) quote = '';
        continue;
      }
      if (ch === '"' || ch === "'") {
        quote = ch;
        current += ch;
        continue;
      }
      if (ch === ',') {
        args.push(current.trim());
        current = '';
        continue;
      }
      current += ch;
    }
    if (current.trim()) args.push(current.trim());
    return args;
  };

  const decodeString = token => {
    const quote = token[0];
    if ((quote !== '"' && quote !== "'") || token[token.length - 1] !== quote) return undefined;
    const body = token.slice(1, -1);
    if (/\\(?![\\'"nrt])/u.test(body)) return undefined;
    return body
      .replace(/\\n/g, '\n')
      .replace(/\\r/g, '\r')
      .replace(/\\t/g, '\t')
      .replace(/\\'/g, "'")
      .replace(/\\"/g, '"')
      .replace(/\\\\/g, '\\');
  };

  const parseArg = (token, element) => {
    if (token === 'this') return { ok: true, value: element };
    if (token === 'null') return { ok: true, value: null };
    if (token === 'true') return { ok: true, value: true };
    if (token === 'false') return { ok: true, value: false };
    if (/^-?\d+(?:\.\d+)?$/.test(token)) return { ok: true, value: Number(token) };
    const value = decodeString(token);
    if (value !== undefined) return { ok: true, value };
    return { ok: false };
  };

  const parseHandler = (source, element) => {
    const match = String(source || '').trim().match(/^([A-Za-z_$][\w$]*)\s*\((.*)\)\s*;?$/s);
    if (!match || !ALLOWED.has(match[1])) return null;
    const rawArgs = match[2].trim();
    const args = [];
    if (rawArgs) {
      for (const token of splitArgs(rawArgs)) {
        const parsed = parseArg(token, element);
        if (!parsed.ok) return null;
        args.push(parsed.value);
      }
    }
    return { fnName: match[1], args };
  };

  const bind = element => {
    const source = element.getAttribute('onclick');
    if (!source) return;
    const parsed = parseHandler(source, element);
    element.removeAttribute('onclick');
    if (!parsed) {
      console.warn('OmniXML: handler inline não migrado foi bloqueado.', source);
      return;
    }
    element.addEventListener('click', event => {
      const fn = window[parsed.fnName];
      if (typeof fn !== 'function') {
        console.error(`OmniXML: ação ${parsed.fnName} indisponível.`);
        return;
      }
      fn.apply(element, parsed.args.map(arg => arg === element ? element : arg));
      if (element.tagName === 'A' && element.getAttribute('href') === '#') event.preventDefault();
    });
  };

  const migrate = root => {
    if (!root?.querySelectorAll) return;
    if (root.nodeType === Node.ELEMENT_NODE && root.hasAttribute?.('onclick')) bind(root);
    root.querySelectorAll('[onclick]').forEach(bind);
  };

  const syncDashboardPreviewV25 = () => {
    const summary = document.getElementById('faixa-resumo-auditoria');
    const preview = document.getElementById('dashboard-preview-v24');
    const real = document.getElementById('dashboard-real-v24');
    if (!summary || !preview || !real) return;
    const hasRealAudit = !summary.classList.contains('hidden');
    preview.classList.toggle('hidden', hasRealAudit);
    real.classList.toggle('hidden', !hasRealAudit);
  };

  const loadSpedLocalV26 = () => {
    if (document.querySelector('script[data-omnixml-sped-local-v26]')) return;
    const script = document.createElement('script');
    script.src = '/static/sped_local_v26.js?v=1';
    script.dataset.omnixmlSpedLocalV26 = '1';
    script.defer = true;
    document.head.appendChild(script);
  };

  const start = () => {
    migrate(document);
    const observer = new MutationObserver(records => {
      for (const record of records) {
        for (const added of record.addedNodes) {
          if (added.nodeType === Node.ELEMENT_NODE) migrate(added);
        }
      }
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });

    syncDashboardPreviewV25();
    const auditSummary = document.getElementById('faixa-resumo-auditoria');
    if (auditSummary) {
      const dashboardObserver = new MutationObserver(syncDashboardPreviewV25);
      dashboardObserver.observe(auditSummary, { attributes: true, attributeFilter: ['class'] });
    }

    loadSpedLocalV26();
    window.__omnixmlInlineHandlersMigrated = true;
    window.__omnixmlDashboardStateV25 = { sync: syncDashboardPreviewV25 };
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
