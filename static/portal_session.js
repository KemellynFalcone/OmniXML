'use strict';
(async () => {
  try {
    const response = await fetch('/api/access/session', {credentials:'same-origin'});
    const info = await response.json();
    if (!info.authenticated) { location.replace('/login'); return; }
    const bar = document.createElement('div');
    bar.className = 'portal-session';
    const heading = document.createElement('strong');
    heading.className = 'portal-session-heading';
    heading.textContent = 'Conta conectada';
    bar.append(heading);
    const name = document.createElement('span');
    name.className = 'portal-session-email';
    name.textContent = info.email;
    bar.append(name);
    if (info.admin && location.pathname === '/') {
      const admin = document.createElement('a');
      admin.href = '/admin'; admin.textContent = 'Administração'; bar.append(admin);
    }
    const logout = document.createElement('button');
    logout.type = 'button'; logout.textContent = '↪ Sair do sistema';
    logout.addEventListener('click', async () => {
      logout.disabled = true;
      try {
        const result = await fetch('/api/access/logout', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});
        if (!result.ok) throw new Error();
        location.replace('/login');
      } catch { logout.disabled = false; logout.textContent = 'Tentar sair novamente'; }
    });
    bar.append(logout);
    const workspace = document.querySelector('main');
    if (workspace) {
      const credit = document.createElement('footer');
      credit.className = 'portal-credit';
      credit.append(document.createTextNode('Desenvolvido por '));
      const developer = document.createElement('strong');
      developer.textContent = 'Kasfalcone';
      credit.append(developer);
      workspace.append(credit);
    }
    const sidebar = document.querySelector('#main-sidebar, .app-sidebar');
    if (sidebar) {
      const footer = sidebar.querySelector('.sidebar-footer, #footer-collapsed')?.parentElement;
      if (sidebar.classList.contains('app-sidebar')) sidebar.querySelector('.sidebar-footer')?.remove();
      if (footer && sidebar.id === 'main-sidebar') footer.replaceChildren(bar);
      else sidebar.append(bar);
    }
  } catch { location.replace('/login'); }
})();
