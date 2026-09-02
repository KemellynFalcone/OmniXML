(() => {
  const BLOCKED_TAGS = new Set(['SCRIPT', 'IFRAME', 'OBJECT', 'EMBED', 'BASE']);
  const URL_ATTRS = new Set(['href', 'src', 'xlink:href', 'formaction']);
  const SAFE_SEFAZ_HOST_SUFFIXES = [
    'fazenda.gov.br',
    'sefaz.gov.br',
    'sefin.ro.gov.br',
    'sefaznet.ac.gov.br',
    'sefaz.am.gov.br',
    'sefaz.rr.gov.br',
    'sefa.pa.gov.br',
    'sefaz.ap.gov.br',
    'sefaz.to.gov.br',
    'sefaz.ma.gov.br',
    'sefaz.pi.gov.br',
    'sefaz.ce.gov.br',
    'set.rn.gov.br',
    'receita.pb.gov.br',
    'sefaz.pe.gov.br',
    'sefaz.al.gov.br',
    'nfce.se.gov.br',
    'sefaz.ba.gov.br',
    'sefaz.es.gov.br',
    'fazenda.rj.gov.br',
    'sefaz.rs.gov.br',
    'dfe.ms.gov.br',
    'sefaz.mt.gov.br',
    'sefaz.go.gov.br',
  ];

  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));

  function dangerousUrl(value) {
    const normalized = String(value || '').trim().replace(/[\u0000-\u001F\u007F\s]+/g, '').toLowerCase();
    return normalized.startsWith('javascript:') ||
      normalized.startsWith('vbscript:') ||
      normalized.startsWith('data:text/html') ||
      normalized.startsWith('data:application/xhtml+xml');
  }

  function hardenElement(element) {
    if (!(element instanceof Element)) return;
    if (BLOCKED_TAGS.has(element.tagName)) {
      element.remove();
      return;
    }
    for (const attr of Array.from(element.attributes || [])) {
      const name = attr.name.toLowerCase();
      if (name.startsWith('on') || name === 'srcdoc') {
        element.removeAttribute(attr.name);
        continue;
      }
      if (URL_ATTRS.has(name) && dangerousUrl(attr.value)) {
        element.removeAttribute(attr.name);
      }
    }
  }

  function hardenTree(root) {
    if (!(root instanceof Element)) return;
    hardenElement(root);
    if (!root.isConnected && BLOCKED_TAGS.has(root.tagName)) return;
    root.querySelectorAll?.('*').forEach(hardenElement);
  }

  function isAllowedExternalUrl(value) {
    try {
      const url = new URL(String(value || ''), window.location.href);
      if (url.origin === window.location.origin) return true;
      if (!['http:', 'https:'].includes(url.protocol)) return false;
      const host = url.hostname.toLowerCase();
      return SAFE_SEFAZ_HOST_SUFFIXES.some(suffix => host === suffix || host.endsWith(`.${suffix}`));
    } catch (_) {
      return false;
    }
  }

  function wrapSefazNavigation() {
    if (typeof window.copiarEAbrir !== 'function' || window.copiarEAbrir.__omnixmlSecurityV3) return false;
    const original = window.copiarEAbrir;
    const guarded = function(chave, url) {
      const key = String(chave || '').replace(/\D/g, '');
      if (key.length !== 44) {
        window.alert('Chave de acesso inválida. A navegação externa foi bloqueada por segurança.');
        return;
      }
      if (!isAllowedExternalUrl(url)) {
        window.alert('Destino externo não autorizado pelo OmniXML.');
        return;
      }
      return original.call(this, key, url);
    };
    guarded.__omnixmlSecurityV3 = true;
    window.copiarEAbrir = guarded;
    return true;
  }

  document.addEventListener('click', event => {
    const anchor = event.target?.closest?.('a[href]');
    if (!anchor) return;
    if (dangerousUrl(anchor.getAttribute('href'))) {
      event.preventDefault();
      event.stopImmediatePropagation();
      console.warn('OmniXML: navegação com esquema perigoso bloqueada.');
    }
  }, true);

  const observer = new MutationObserver(records => {
    for (const record of records) {
      for (const node of record.addedNodes || []) {
        if (node instanceof Element) hardenTree(node);
      }
    }
  });

  function start() {
    hardenTree(document.documentElement);
    observer.observe(document.documentElement, { childList: true, subtree: true });
    let attempts = 0;
    const timer = setInterval(() => {
      if (wrapSefazNavigation() || ++attempts > 80) clearInterval(timer);
    }, 100);
  }

  window.__omnixmlSecurityV3 = {
    escapeHtml,
    dangerousUrl,
    isAllowedExternalUrl,
    hardenTree,
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
