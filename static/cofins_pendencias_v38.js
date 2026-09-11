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

  function defaultStatus(modal) {
    const diagnosis = modal.querySelector('.cofins-auditor-v37__guidance-row span')?.textContent || '';
    if (/conciliado/i.test(diagnosis)) return 'Conciliado';
    if (/base de cálculo divergente/i.test(diagnosis)) return 'Revisar';
    return 'Crítico';
  }

  function formatDate(value) {
    if (!value) return 'Ainda não revisado';
    try { return new Date(value).toLocaleString('pt-BR'); }
    catch (_) { return value; }
  }

  function badge(status) {
    const map = {
      'Crítico': 'background:#fee2e2;color:#991b1b;border-color:#fecaca',
      'Revisar': 'background:#fef3c7;color:#92400e;border-color:#fde68a',
      'Conciliado': 'background:#dcfce7;color:#166534;border-color:#bbf7d0',
      'Justificado': 'background:#dbeafe;color:#1d4ed8;border-color:#bfdbfe'
    };
    return `<span style="display:inline-flex;padding:4px 8px;border-radius:999px;border:1px solid;font-size:11px;font-weight:800;${map[status] || map.Revisar}">${status}</span>`;
  }

  function renderQueue() {
    const section = document.getElementById('cofins-auditor-v34');
    if (!section) return;

    let panel = document.getElementById('cofins-pendencias-v38');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'cofins-pendencias-v38';
      panel.style.cssText = 'margin:12px 0 16px;padding:14px;border:1px solid #e2e8f0;border-radius:12px;background:#fff';
      section.prepend(panel);
    }

    const items = Object.values(readStore());
    const counts = STATUS.reduce((acc, s) => ({ ...acc, [s]: items.filter(i => i.status === s).length }), {});
    const signature = JSON.stringify(counts);
    if (panel.dataset.renderSignature === signature) return;
    panel.dataset.renderSignature = signature;

    panel.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap">
        <div>
          <div style="font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#2563eb">v38 · Classificação e Pendências</div>
          <strong style="display:block;color:#0f172a;margin-top:3px">Fila de revisão fiscal</strong>
          <span style="font-size:12px;color:#64748b">Tratativas salvas neste navegador.</span>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          ${STATUS.map(s => badge(`${s}: ${counts[s] || 0}`.replace(/: 0$/, ': 0'))).join('')}
        </div>
      </div>`;
  }

  function injectTreatment(modal) {
    if (!modal || modal.querySelector('#cofins-tratativa-v38')) return;
    const content = modal.querySelector('.cofins-auditor-v35__content');
    if (!content) return;

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
    });
  }

  const observer = new MutationObserver(records => {
    let shouldRenderQueue = false;
    let modal = null;

    for (const record of records) {
      for (const node of Array.from(record.addedNodes || [])) {
        if (node?.nodeType !== Node.ELEMENT_NODE) continue;
        if (node.id === 'cofins-auditor-v34' || node.querySelector?.('#cofins-auditor-v34')) {
          shouldRenderQueue = true;
        }
        if (node.id === 'cofins-auditor-v35-modal') modal = node;
        else if (!modal) modal = node.querySelector?.('#cofins-auditor-v35-modal') || null;
      }
    }

    if (shouldRenderQueue) renderQueue();
    if (modal) injectTreatment(modal);
  });

  observer.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderQueue, { once: true });
  else renderQueue();
  window.OmniXMLCofinsPendenciasV38 = { readStore, renderQueue };
})();