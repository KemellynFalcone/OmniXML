(() => {
  'use strict';

  document.addEventListener('click', event => {
    const button = event.target?.closest?.('button[data-omnixml-sefaz-chave][data-omnixml-sefaz-url]');
    if (!button) return;

    event.preventDefault();
    const chave = String(button.dataset.omnixmlSefazChave || '').replace(/\D/g, '');
    const url = String(button.dataset.omnixmlSefazUrl || '');

    if (chave.length !== 44) {
      window.alert('Chave de acesso inválida. A consulta foi bloqueada por segurança.');
      return;
    }
    if (typeof window.copiarEAbrir !== 'function') {
      console.error('OmniXML: ação segura de consulta SEFAZ indisponível.');
      return;
    }
    window.copiarEAbrir(chave, url);
  });

  window.__omnixmlSafeRenderersV8 = true;
})();
