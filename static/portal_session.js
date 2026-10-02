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
      admin.href = '/admin'; admin.title = 'Administração';
      admin.setAttribute('aria-label', 'Administração');
      const icon = document.createElement('span');
      icon.className = 'portal-action-icon'; icon.textContent = '⚙'; icon.setAttribute('aria-hidden', 'true');
      const label = document.createElement('span');
      label.className = 'portal-action-label'; label.textContent = 'Administração';
      admin.append(icon, label); bar.append(admin);
    }
    const logout = document.createElement('button');
    logout.type = 'button'; logout.title = 'Sair do sistema';
    logout.setAttribute('aria-label', 'Sair do sistema');
    const logoutIcon = document.createElement('span');
    logoutIcon.className = 'portal-action-icon'; logoutIcon.textContent = '↪'; logoutIcon.setAttribute('aria-hidden', 'true');
    const logoutLabel = document.createElement('span');
    logoutLabel.className = 'portal-action-label'; logoutLabel.textContent = 'Sair do sistema';
    logout.append(logoutIcon, logoutLabel);
    logout.addEventListener('click', async () => {
      logout.disabled = true;
      try {
        const result = await fetch('/api/access/logout', {method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});
        if (!result.ok) throw new Error();
        location.replace('/login');
      } catch { logout.disabled = false; logoutLabel.textContent = 'Tentar sair novamente'; logout.title = 'Tentar sair novamente'; }
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
