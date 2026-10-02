'use strict';
(async () => {
  try {
    const response = await fetch('/api/access/session', {credentials:'same-origin'});
    const info = await response.json();
    if (!info.authenticated) { location.replace('/login'); return; }
    const bar = document.createElement('div');
    bar.className = 'portal-session';
    const name = document.createElement('span');
    name.textContent = info.email;
    bar.append(name);
    if (info.admin) {
      const admin = document.createElement('a');
      admin.href = '/admin'; admin.textContent = 'Administração'; bar.append(admin);
    }
    const logout = document.createElement('button');
    logout.type = 'button'; logout.textContent = 'Sair';
    logout.addEventListener('click', async () => {
      logout.disabled = true;
      try {
        const result = await fetch('/api/access/logout', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});
        if (!result.ok) throw new Error();
        location.replace('/login');
      } catch { logout.disabled = false; logout.textContent = 'Tentar sair novamente'; }
    });
    bar.append(logout); document.body.prepend(bar);
  } catch { location.replace('/login'); }
})();
