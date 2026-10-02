'use strict';
(() => {
  const el = id => document.getElementById(id);
  let authenticated = false, configured = false, codeStep = false, busy = false;
  function showStep(code) {
    codeStep = code;
    if (!el('email-step')) return;
    el('email-step').hidden = code; el('code-step').hidden = !code;
    el('access-email').required = !code; el('access-code').required = code;
    el('code-destination').textContent = `Código enviado para ${el('access-email').value.trim()}.`;
    (code ? el('access-code') : el('access-email')).focus();
  }
  async function accessState() {
    const response = await fetch('/api/access/session', {credentials:'same-origin'});
    const info = await response.json();
    authenticated = info.authenticated; configured = info.configured;
    el('access-message').textContent = info.authenticated ? `Conectado como ${info.email}. Acesso válido por até 8 horas.` : info.configured ? (document.body.dataset.page === 'login' ? 'Informe seu e-mail para receber o código.' : 'Entre por e-mail para recuperar XMLs.') : 'Acesso por e-mail ainda não configurado. Use o acesso administrativo.';
    if (el('admin-link')) el('admin-link').hidden = !info.admin;
    if (document.body.dataset.page === 'login' && authenticated) { window.location.replace('/'); return; }
    el('access-logout').hidden = !info.authenticated;
    ['access-email','access-code','access-send','access-verify'].forEach(id => { el(id).disabled = info.authenticated || !info.configured; });
  }
  async function accessAction(action, button) {
    if (busy) return;
    busy = true; button.disabled = true;
    if (el('change-email')) el('change-email').disabled = true;
    try {
      const response = await fetch('/api/access/'+action, {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:el('access-email').value,code:el('access-code').value})});
      const info = await response.json();
      if (!response.ok) throw new Error(info.error || 'Não foi possível concluir.');
      if (action !== 'code') { el('access-code').value = ''; await accessState(); }
      else { el('access-message').textContent = info.message; if (el('email-step')) showStep(true); }
      if (action === 'logout') window.location.replace('/login');
    } catch (error) { el('access-message').textContent = error.message || 'Falha na conexão.'; }
    finally { busy = false; if (el('change-email')) el('change-email').disabled = false; button.disabled = button.id === 'access-logout' ? false : authenticated || !configured; }
  }
  if (el('login-form')) {
    el('login-form').addEventListener('submit', event => {
      event.preventDefault();
      accessAction(codeStep ? 'verify' : 'code', el(codeStep ? 'access-verify' : 'access-send'));
    });
    el('change-email').addEventListener('click', () => {
      el('access-code').value = ''; showStep(false);
      el('access-message').textContent = 'Informe seu e-mail para receber o código.';
    });
  } else {
    el('access-send').addEventListener('click', event => accessAction('code',event.currentTarget));
    el('access-verify').addEventListener('click',event => accessAction('verify',event.currentTarget));
  }
  el('access-logout').addEventListener('click',event => accessAction('logout',event.currentTarget));
  accessState().catch(() => { el('access-message').textContent = 'Não foi possível verificar o acesso.'; });
})();
