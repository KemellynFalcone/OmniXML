(() => {
  'use strict';

  const STORAGE_KEY = 'omnixml:cofins:pendencias:v38';
  const STATUS = ['Crítico', 'Revisar', 'Conciliado', 'Justificado'];

  const readStore = () => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch (_) { return {}; }
  };

  const writeStore = data => localStorage.setItem(STORAGE_KEY, JSON.stringify(data));

  function keyFromModal(modal) {
    const title = modal.querySelector('.cofins-auditor-v35__header h5')?.textContent || '';
    const cst = title.match(/CST\s+([^\s/]+)/i)?.[1] || 'N/A';
    const cfop = title.match(/CFOP\s+([^\s]+)/i)?.[1] || 'N/A';
    return { key: `${cst}|${cfop}`, cst, cfop };
  }

  function defaultStatusFromDiagnosis(diagnosis) {
    const text = String(diagnosis || '');
    if (/conciliado/i.test(text)) return 'Conciliado';
    if (/base de cálculo divergente|arredondamento/i.test(text)) return 'Revisar';
    return 'Crítico';
  }

  function defaultStatus(modal) {
    const diagnosis = modal.querySelector('.cofins-auditor-v37__guidance-row span')?.textContent || '';
    return defaultStatusFromDiagnosis(diagnosis);
  }

  function formatDate(value) {
    if (!value) return 'Ainda não revisado';
    try { return new Date(value).toLocaleString('pt-BR'); }
    catch (_) { return value; }
  }

  function badge(status, label = status) {
    const map = {
      'Crítico': 'background:#fee2e2;color:#991b1b;border-color:#fecaca',
      'Revisar': 'background:#fef3c7;color:#92400e;border-color:#fde68a',
      'Conciliado': 'background:#dcfce7;color:#166534;border-color:#bbf7d0',
      'Justificado': 'background:#dbeafe;color:#1d4ed8;border-color:#bfdbfe'
    };
    return `<span style="display:inline-flex;padding:4px 9px;border-radius:999px;border:1px solid;font-size:11px;font-weight:800;${map[status] || map.Revisar}">${label}</span>`;
  }

  function auditItems() {
    const groups = Array.isArray(window.__omnixmlCofinsAuditorV34?.groups)
      ? window.__omnixmlCofinsAuditorV34.groups
      : [];
    const store = readStore();

    return groups.map(group => {
      const cst = String(group?.cst || group?.cst_cofins || 'N/A');
      const cfop = String(group?.cfop || 'N/A');
      const key = `${cst}|${cfop}`;
      const saved = store[key];
      return {
        key,
        cst,
        cfop,
        status: saved?.status || defaultStatusFromDiagnosis(group?.cause || group?.diagnostico),
        justificativa: saved?.justificativa || '',
        atualizado_em: saved?.atualizado_em || '',
        persisted: Boolean(saved)
      };
    });
  }

  function renderQueue() {
    const host = document.getElementById('res-pis-cofins');
    if (!host) return false;

    const items = auditItems();
    let panel = document.getElementById('cofins-pendencias-v38');

    if (!items.length) {
      panel?.remove();
      return false;
    }

    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'cofins-pendencias-v38';
      panel.style.cssText = 'margin:8px 0 10px;padding:10px 12px;border:1px solid #dbe3ef;border-left:4px solid #2563eb;border-radius:10px;background:#f8fafc';
    }

    const auditor = document.getElementById('cofins-auditor-v34');
    if (auditor?.parentNode) auditor.parentNode.insertBefore(panel, auditor);
    else if (!panel.parentNode) host.prepend(panel);

    const counts = STATUS.reduce((acc, status) => ({
      ...acc,
      [status]: items.filter(item => item.status === status).length
    }), {});
    const pending = (counts['Crítico'] || 0) + (counts['Revisar'] || 0);
    const resolved = (counts['Conciliado'] || 0) + (counts['Justificado'] || 0);
    const signature = JSON.stringify({ counts, pending, resolved, keys: items.map(item => item.key) });
    if (panel.dataset.renderSignature === signature) return true;
    panel.dataset.renderSignature = signature;

    const visibleBadges = STATUS
      .filter(status => (counts[status] || 0) > 0)
      .map(status => badge(status, `${status}: ${counts[status]}`))
      .join('');

    panel.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:9px;min-width:240px">
          <div style="width:30px;height:30px;border-radius:8px;background:#dbeafe;color:#1d4ed8;display:flex;align-items:center;justify-content:center;font-weight:900">!</div>
          <div>
            <strong style="display:block;color:#0f172a;font-size:13px">${pending} pendência${pending === 1 ? '' : 's'} para revisão</strong>
            <span style="font-size:11px;color:#64748b">${items.length} divergência${items.length === 1 ? '' : 's'} identificada${items.length === 1 ? '' : 's'} nesta auditoria${resolved ? ` · ${resolved} tratada${resolved === 1 ? '' : 's'}` : ''}</span>
          </div>
        </div>
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">${visibleBadges}</div>
      </div>`;
    return true;
  }

  function injectTreatment(modal) {
    if (!modal || modal.querySelector('#cofins-tratativa-v38')) return false;
    const content = modal.querySelector('.cofins-auditor-v35__content');
    if (!content) return false;

    const { key, cst, cfop } = keyFromModal(modal);
    const store = readStore();
    const saved = store[key] || { status: defaultStatus(modal), justificativa: '', atualizado_em: '' };

    const wrap = document.createElement('div');
    wrap.id = 'cofins-tratativa-v38';
    wrap.style.cssText = 'margin:14px 0;padding:14px;border:1px solid #dbeafe;border-radius:12px;background:#f8fbff';
    wrap.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start;flex-wrap:wrap">
        <div>
          <strong style="color:#0f172a">Tratativa da pendência</strong>
          <div style="font-size:12px;color:#64748b;margin-top:2px">CST ${cst} / CFOP ${cfop}</div>
        </div>
        <div id="cofins-v38-current-badge">${badge(saved.status)}</div>
      </div>
      <div style="display:grid;grid-template-columns:220px 1fr;gap:12px;margin-top:12px">
        <label style="font-size:12px;color:#475569;font-weight:700">Status
          <select id="cofins-v38-status" style="display:block;width:100%;margin-top:5px;border:1px solid #cbd5e1;border-radius:8px;padding:8px;background:#fff;color:#0f172a">
            ${STATUS.map(s => `<option ${saved.status === s ? 'selected' : ''}>${s}</option>`).join('')}
          </select>
        </label>
        <label style="font-size:12px;color:#475569;font-weight:700">Justificativa / observação
          <textarea id="cofins-v38-justificativa" rows="3" placeholder="Ex.: Divergência validada com a contabilidade; ajuste já refletido na apuração..." style="display:block;width:100%;margin-top:5px;border:1px solid #cbd5e1;border-radius:8px;padding:8px;background:#fff;color:#0f172a;resize:vertical">${saved.justificativa || ''}</textarea>
        </label>
      </div>
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:10px;flex-wrap:wrap">
        <small id="cofins-v38-updated" style="color:#64748b">Última revisão: ${formatDate(saved.atualizado_em)}</small>
        <button id="cofins-v38-save" type="button" style="border:0;border-radius:8px;background:#2563eb;color:#fff;padding:8px 12px;font-size:12px;font-weight:800;cursor:pointer">Salvar tratativa</button>
      </div>`;

    content.insertBefore(wrap, content.children[1] || null);

    wrap.querySelector('#cofins-v38-save').addEventListener('click', () => {
      const status = wrap.querySelector('#cofins-v38-status').value;
      const justificativa = wrap.querySelector('#cofins-v38-justificativa').value.trim();
      if (status === 'Justificado' && !justificativa) {
        alert('Para marcar como Justificado, informe o motivo da justificativa.');
        return;
      }

      const data = readStore();
      data[key] = {
        cst,
        cfop,
        status,
        justificativa,
        atualizado_em: new Date().toISOString()
      };
      writeStore(data);
      wrap.querySelector('#cofins-v38-current-badge').innerHTML = badge(status);
      wrap.querySelector('#cofins-v38-updated').textContent = `Última revisão: ${formatDate(data[key].atualizado_em)}`;
      const panel = document.getElementById('cofins-pendencias-v38');
      if (panel) delete panel.dataset.renderSignature;
      renderQueue();
      document.dispatchEvent(new CustomEvent('omnixml:cofins-pendency-updated', { detail: { key, cst, cfop, status } }));
    });
    return true;
  }

  function install() {
    renderQueue();

    document.addEventListener('click', event => {
      if (!event.target.closest('[data-cofins-details]')) return;
      renderQueue();
      requestAnimationFrame(() => {
        const modal = document.getElementById('cofins-auditor-v35-modal');
        if (modal) injectTreatment(modal);
      });
    });

    document.addEventListener('omnixml:cofins-audit-ready', renderQueue);
    window.OmniXMLCofinsPendenciasV38 = { readStore, renderQueue, injectTreatment, auditItems };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
