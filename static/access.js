'use strict';
(() => {
  const el = id => document.getElementById(id);
  const activating = document.body.dataset.page === 'activate';
  // Keep the invitation out of URL logs, referrers and browser history.
  const invite = activating ? window.location.hash.slice(1) : '';
  if (activating) window.history.replaceState(null, '', '/activate');
  let busy = false, widget = null;
  const captcha = el('access-captcha');
  if (captcha) {
    el('access-submit').disabled = true;
    window.omniCaptchaReady = () => {
      widget = window.grecaptcha.render(captcha, {
        sitekey: captcha.dataset.sitekey,
        size: window.innerWidth < 380 ? 'compact' : 'normal',
        callback: () => { el('access-submit').disabled = busy; },
        'expired-callback': () => { el('access-submit').disabled = true; },
        'error-callback': () => { el('access-message').textContent = 'Proteção indisponível. Atualize a página e tente novamente.'; el('access-submit').disabled = true; }
      });
    };
    const script = document.createElement('script');
    script.src = 'https://www.google.com/recaptcha/api.js?onload=omniCaptchaReady&render=explicit&hl=pt-BR';
    script.async = true;
    script.onerror = () => { el('access-message').textContent = 'Não foi possível carregar a proteção. Verifique a conexão e tente novamente.'; };
    document.head.append(script);
  }
  if (activating && !invite) {
    el('access-message').textContent = 'Abra o link individual fornecido pelo administrador.';
    el('access-submit').disabled = true;
  }
  el('login-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || (activating && !invite)) return;
    if (activating && el('access-password').value !== el('access-confirm').value) {
      el('access-message').textContent = 'As senhas precisam ser iguais.'; return;
    }
    busy = true; el('access-submit').disabled = true;
    el('access-message').textContent = activating ? 'Salvando sua senha…' : 'Verificando acesso…';
    try {
      const response = await fetch('/api/access/'+(activating ? 'activate' : 'login'), {
        method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({email:el('access-email')?.value, password:el('access-password').value, invite,
          captcha:widget === null ? '' : window.grecaptcha.getResponse(widget)})
      });
      const info = await response.json();
      if (!response.ok) throw new Error(info.error || 'Não foi possível concluir.');
      el('access-password').value = '';
      window.location.replace(activating ? '/login' : '/');
    } catch (error) {
      el('access-message').textContent = error.message || 'Falha na conexão. Tente novamente.';
      if (widget !== null) window.grecaptcha.reset(widget);
    } finally {
      busy = false; el('access-submit').disabled = !!captcha || (activating && !invite);
    }
  });
})();
