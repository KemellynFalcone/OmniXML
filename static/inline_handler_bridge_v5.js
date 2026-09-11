(() => {
  'use strict';

  const ALLOWED = new Set([
    'fecharModalProduto','mudarAba','iniciarProcessamento','filtrarPeloCard','filtrarCancelados',
    'filtrarInconsistencias','filtrarErros','toggleSidebar','limparESairCliente','exportarRelatorioGeral',
    'importarPisCofins','confrontarSPED','mostrarDivergencias','abrirModalProduto','copiarEAbrir'
  ]);

  const splitArgs = raw => {
    const args = [];
    let current = '', quote = '', escaped = false;
    for (const ch of raw) {
      if (escaped) { current += ch; escaped = false; continue; }
      if (ch === '\\') { current += ch; escaped = true; continue; }
      if (quote) { current += ch; if (ch === quote) quote = ''; continue; }
      if (ch === '"' || ch === "'") { quote = ch; current += ch; continue; }
      if (ch === ',') { args.push(current.trim()); current = ''; continue; }
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
    return body.replace(/\\n/g, '\n').replace(/\\r/g, '\r').replace(/\\t/g, '\t')
      .replace(/\\'/g, "'").replace(/\\"/g, '"').replace(/\\\\/g, '\\');
  };

  const parseArg = (token, element) => {
    if (token === 'this') return { ok: true, value: element };
    if (token === 'null') return { ok: true, value: null };
    if (token === 'true') return { ok: true, value: true };
    if (token === 'false') return { ok: true, value: false };
    if (/^-?\d+(?:\.\d+)?$/.test(token)) return { ok: true, value: Number(token) };
    const value = decodeString(token);
    return value !== undefined ? { ok: true, value } : { ok: false };
  };

  const parseHandler = (source, element) => {
    const match = String(source || '').trim().match(/^([A-Za-z_$][\w$]*)\s*\((.*)\)\s*;?$/s);
    if (!match || !ALLOWED.has(match[1])) return null;
    const args = [];
    if (match[2].trim()) {
      for (const token of splitArgs(match[2].trim())) {
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
    if (!parsed) { console.warn('OmniXML: handler inline não migrado foi bloqueado.', source); return; }
    element.addEventListener('click', event => {
      const fn = window[parsed.fnName];
      if (typeof fn !== 'function') { console.error(`OmniXML: ação ${parsed.fnName} indisponível.`); return; }
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
    if (preview) preview.classList.add('hidden');
    if (!summary || !real) return;
    const hasRealAudit = !summary.classList.contains('hidden');
    real.classList.toggle('hidden', !hasRealAudit);
  };

  const loadScript = (selector, src, dataKey) => {
    if (document.querySelector(selector)) return;
    const script = document.createElement('script');
    script.src = src;
    script.dataset[dataKey] = '1';
    script.defer = true;
    document.head.appendChild(script);
  };

  const loadCssV30 = () => {
    if (document.querySelector('link[data-omnixml-ux-v30]')) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/ux_cleanup_v30.css?v=1';
    link.dataset.omnixmlUxV30 = '1';
    document.head.appendChild(link);
  };

  const loadCofinsAuditorV34 = () => {
    if (!document.querySelector('link[data-omnixml-cofins-auditor-v34]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/static/cofins_auditor_v34.css?v=1';
      link.dataset.omnixmlCofinsAuditorV34 = '1';
      document.head.appendChild(link);
    }
    loadScript('script[data-omnixml-cofins-auditor-v34]', '/static/cofins_auditor_v34.js?v=1', 'omnixmlCofinsAuditorV34');
  };

  const loadCofinsPendenciasV38 = () => loadScript(
    'script[data-omnixml-cofins-pendencias-v38]', '/static/cofins_pendencias_v38.js?v=1', 'omnixmlCofinsPendenciasV38'
  );

  const ENABLE_COFINS_PENDENCIAS_V38 = false;

  const loadCofinsOrigemV39 = () => loadScript(
    'script[data-omnixml-cofins-origem-v39]', '/static/cofins_origem_v39.js?v=1', 'omnixmlCofinsOrigemV39'
  );

  const loadBlocoMV40 = () => loadScript(
    'script[data-omnixml-bloco-m-v40]', '/static/bloco_m_v40.js?v=1', 'omnixmlBlocoMV40'
  );

  const loadBlocoMArredondamentoV401 = () => loadScript(
    'script[data-omnixml-bloco-m-arredondamento-v40-1]', '/static/bloco_m_arredondamento_v40_1.js?v=1', 'omnixmlBlocoMArredondamentoV401'
  );

  const loadBlocoMVisualV402 = () => {
    if (!document.querySelector('link[data-omnixml-bloco-m-visual-v40-2]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/static/bloco_m_visual_v40_2.css?v=1';
      link.dataset.omnixmlBlocoMVisualV402 = '1';
      document.head.appendChild(link);
    }
    loadScript(
      'script[data-omnixml-bloco-m-visual-v40-2]',
      '/static/bloco_m_visual_v40_2.js?v=1',
      'omnixmlBlocoMVisualV402'
    );
  };

  const loadFailureReconciliationV27 = () => loadScript(
    'script[data-omnixml-failure-reconciliation-v27]', '/static/failure_reconciliation_v27.js?v=1', 'omnixmlFailureReconciliationV27'
  );
  const loadRetailOriginV28 = () => loadScript(
    'script[data-omnixml-retail-origin-v28]', '/static/retail_origin_v28.js?v=1', 'omnixmlRetailOriginV28'
  );
  const loadXmlPisCofinsV30 = () => loadScript(
    'script[data-omnixml-xml-pis-cofins-v30]', '/static/pis_cofins_xml_v30.js?v=1', 'omnixmlXmlPisCofinsV30'
  );

  const loadSpedLocalV26 = () => {
    if (document.querySelector('script[data-omnixml-sped-local-v26]')) return;
    const script = document.createElement('script');
    script.src = '/static/sped_local_v26.js?v=1';
    script.dataset.omnixmlSpedLocalV26 = '1';
    script.defer = true;
    document.head.appendChild(script);
  };

  const loadEfdContribLocalV29 = () => {
    if (document.querySelector('script[data-omnixml-efd-contrib-local-v29]')) return;
    const script = document.createElement('script');
    script.src = '/static/sped_contrib_local_v29.js?v=1';
    script.dataset.omnixmlEfdContribLocalV29 = '1';
    script.defer = true;
    document.head.appendChild(script);
  };

  const start = () => {
    migrate(document);
    const observer = new MutationObserver(records => {
      for (const record of records) for (const added of record.addedNodes) {
        if (added.nodeType === Node.ELEMENT_NODE) migrate(added);
      }
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });

    loadCssV30();
    syncDashboardPreviewV25();
    const auditSummary = document.getElementById('faixa-resumo-auditoria');
    if (auditSummary) {
      const dashboardObserver = new MutationObserver(syncDashboardPreviewV25);
      dashboardObserver.observe(auditSummary, { attributes: true, attributeFilter: ['class'] });
    }

    loadFailureReconciliationV27();
    loadRetailOriginV28();
    loadXmlPisCofinsV30();
    loadSpedLocalV26();
    loadEfdContribLocalV29();
    loadCofinsAuditorV34();
    if (ENABLE_COFINS_PENDENCIAS_V38) loadCofinsPendenciasV38();
    loadCofinsOrigemV39();
    loadBlocoMV40();
    loadBlocoMArredondamentoV401();
    loadBlocoMVisualV402();
    window.__omnixmlInlineHandlersMigrated = true;
    window.__omnixmlDashboardStateV25 = { sync: syncDashboardPreviewV25 };
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
