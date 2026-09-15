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
      'Crítico': 'background:#fff1f2;color:#be123c;border-color:#fecdd3',
      'Revisar': 'background:#fffbeb;color:#b45309;border-color:#fde68a',
      'Conciliado': 'background:#ecfdf5;color:#047857;border-color:#a7f3d0',
      'Justificado': 'background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe'
    };
    return `<span style="display:inline-flex;align-items:center;padding:5px 10px;border-radius:999px;border:1px solid;font-size:11px;line-height:1;font-weight:800;white-space:nowrap;${map[status] || map.Revisar}">${label}</span>`;
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
      panel.style.cssText = 'margin:10px 0 12px;padding:12px 14px;border:1px solid #e2e8f0;border-radius:12px;background:#ffffff;box-shadow:0 1px 2px rgba(15,23,42,.04)';
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
      .map(status => badge(status, `${status} ${counts[status]}`))
      .join('');

    const iconBg = pending > 0 ? '#fff7ed' : '#ecfdf5';
    const iconColor = pending > 0 ? '#ea580c' : '#059669';
    const iconSymbol = pending > 0 ? '!' : '✓';
    const title = pending > 0
      ? `${pending} pendência${pending === 1 ? '' : 's'} para revisão`
      : 'Auditoria revisada';
    const subtitle = `${items.length} divergência${items.length === 1 ? '' : 's'} identificada${items.length === 1 ? '' : 's'}${resolved ? ` · ${resolved} tratada${resolved === 1 ? '' : 's'}` : ''}`;

    panel.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:11px;min-width:0;flex:1 1 360px">
          <div style="width:34px;height:34px;flex:0 0 34px;border-radius:10px;background:${iconBg};color:${iconColor};display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900">${iconSymbol}</div>
          <div style="min-width:0">
            <div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap">
              <strong style="color:#0f172a;font-size:14px;line-height:1.2">${title}</strong>
              <span style="font-size:11px;color:#94a3b8">${subtitle}</span>
            </div>
            <span style="display:block;margin-top:3px;font-size:11px;color:#64748b">Revise os grupos abaixo e registre a tratativa em “Ver detalhes”.</span>
          </div>
        </div>
        <div style="display:flex;gap:6px;align-items:center;justify-content:flex-end;flex-wrap:wrap">${visibleBadges}</div>
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
