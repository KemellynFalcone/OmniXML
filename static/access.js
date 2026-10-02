'use strict';
(() => {
  const el = id => document.getElementById(id);
  let authenticated = false, configured = false;
  async function accessState() {
    const response = await fetch('/api/access/session', {credentials:'same-origin'});
    const info = await response.json();
    authenticated = info.authenticated; configured = info.configured;
    el('access-message').textContent = info.authenticated ? `Conectado como ${info.email}. Acesso válido por até 8 horas.` : info.configured ? 'Informe seu e-mail para receber o código.' : 'Acesso por e-mail ainda não configurado. Use o acesso administrativo.';
    el('access-logout').hidden = !info.authenticated;
    ['access-email','access-code','access-send','access-verify'].forEach(id => { el(id).disabled = info.authenticated || !info.configured; });
  }
  async function accessAction(action, button) {
    button.disabled = true;
    try {
      const response = await fetch('/api/access/'+action, {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:el('access-email').value,code:el('access-code').value})});
      const info = await response.json();
      if (!response.ok) throw new Error(info.error || 'Não foi possível concluir.');
      if (action !== 'code') { el('access-code').value = ''; await accessState(); }
      else el('access-message').textContent = info.message;
      if (action === 'logout') window.location.reload();
    } catch (error) { el('access-message').textContent = error.message || 'Falha na conexão.'; }
    finally { button.disabled = button.id === 'access-logout' ? false : authenticated || !configured; }
  }
  el('access-send').addEventListener('click',event => accessAction('code',event.currentTarget));
  el('access-verify').addEventListener('click',event => accessAction('verify',event.currentTarget));
  el('access-logout').addEventListener('click',event => accessAction('logout',event.currentTarget));
  accessState().catch(() => { el('access-message').textContent = 'Não foi possível verificar o acesso.'; });
})();
