(() => {
  'use strict';

  const money = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const STATUS_ORDER = { 'Crítico': 0, 'Revisar': 1, 'Baixo impacto': 2 };

  function causeType(group) {
    const text = String(group?.cause || '').toLowerCase();
    if (text.includes('base e alíquota')) return 'Base de cálculo + Alíquota';
    if (text.includes('base de cálculo')) return 'Base de cálculo';
    if (text.includes('alíquota')) return 'Alíquota';
    if (text.includes('arredondamento')) return 'Arredondamento';
    return 'Valor divergente';
  }

  function secureTrace(group) {
    const xmlRows = Array.isArray(group?.xmlRows) ? group.xmlRows : [];
    const efdRows = Array.isArray(group?.efdRows) ? group.efdRows : [];
    return xmlRows.length > 0 && efdRows.length > 0
      && xmlRows.every(row => String(row?.chave || '').trim())
      && efdRows.every(row => String(row?.chave || '').trim());
  }

  function severity(group) {
    const impact = Math.abs(Number(group?.diff || 0));
    const reference = Math.max(Math.abs(Number(group?.efdValue || 0)), Math.abs(Number(group?.xmlValue || 0)), 1);
    const relative = (impact / reference) * 100;
    const cause = causeType(group);

    if (cause === 'Arredondamento' && impact <= 1) return 'Baixo impacto';
    if (impact >= 100 || (impact >= 10 && relative >= 5)) return 'Crítico';
    if (impact >= 1) return 'Revisar';
    return 'Baixo impacto';
  }

  function actionFor(group) {
    const type = causeType(group);
    if (type === 'Base de cálculo + Alíquota') return 'Revisar base de cálculo, CST e alíquota na escrituração e confrontar com os XMLs antes de qualquer ajuste.';
    if (type === 'Base de cálculo') return 'Revisar composição da base, exclusões, reduções e CST nos registros C170/C175 e nos XMLs.';
    if (type === 'Alíquota') return 'Revisar CST, alíquota aplicada e valor da contribuição no C170/C175; confirmar a composição da apuração.';
    if (type === 'Arredondamento') return 'Validar se a diferença decorre de arredondamento por item versus cálculo consolidado antes de tratar como divergência fiscal.';
    return 'Confrontar o valor escriturado com os documentos e revisar a composição da contribuição antes de qualquer ajuste.';
  }

  function finding(group, index) {
    const impact = Math.abs(Number(group?.diff || 0));
    return {
      key: `${group?.cst || '00'}|${group?.cfop || 'N/A'}`,
      cst: String(group?.cst || '00'),
      cfop: String(group?.cfop || 'N/A'),
      priority: index + 1,
      severity: severity(group),
      causeType: causeType(group),
      impact,
      confidence: secureTrace(group) ? 'Alta' : 'Média',
      action: actionFor(group),
      diagnosis: String(group?.cause || 'Divergência fiscal a revisar')
    };
  }

  function findings() {
    const groups = Array.isArray(window.__omnixmlCofinsAuditorV34?.groups)
      ? window.__omnixmlCofinsAuditorV34.groups
      : [];
    return groups
      .map((group, index) => finding(group, index))
      .sort((a, b) => STATUS_ORDER[a.severity] - STATUS_ORDER[b.severity] || b.impact - a.impact || a.priority - b.priority)
      .map((item, index) => ({ ...item, priority: index + 1 }));
  }

  function badgeClass(level) {
    if (level === 'Crítico') return 'diagnostico-fiscal-v403__badge--critical';
    if (level === 'Revisar') return 'diagnostico-fiscal-v403__badge--review';
    return 'diagnostico-fiscal-v403__badge--low';
  }

  function renderSummary() {
    const auditor = document.getElementById('cofins-auditor-v34');
    if (!auditor?.parentNode) return false;
    const items = findings();
    if (!items.length) {
      document.getElementById('diagnostico-fiscal-v403')?.remove();
      return false;
    }

    let panel = document.getElementById('diagnostico-fiscal-v403');
    if (!panel) {
      panel = document.createElement('section');
      panel.id = 'diagnostico-fiscal-v403';
      panel.className = 'diagnostico-fiscal-v403';
    }
    if (panel.nextElementSibling !== auditor) auditor.parentNode.insertBefore(panel, auditor);

    const totalImpact = items.reduce((sum, item) => sum + item.impact, 0);
    const critical = items.filter(item => item.severity === 'Crítico').length;
    const review = items.filter(item => item.severity === 'Revisar').length;
    const low = items.filter(item => item.severity === 'Baixo impacto').length;
    const causeCounts = items.reduce((acc, item) => {
      acc[item.causeType] = (acc[item.causeType] || 0) + 1;
      return acc;
    }, {});
    const mainCause = Object.entries(causeCounts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0]?.[0] || '—';

    panel.innerHTML = `
      <div class="diagnostico-fiscal-v403__heading">
        <div>
          <span class="diagnostico-fiscal-v403__eyebrow">Diagnóstico Fiscal 2.0</span>
          <strong>Prioridade de revisão</strong>
          <small>Visão única da auditoria: impacto, gravidade e causa provável.</small>
        </div>
      </div>
      <div class="diagnostico-fiscal-v403__metrics">
        <div><span>Impacto estimado</span><strong>${money(totalImpact)}</strong></div>
        <div><span>Críticos</span><strong>${critical}</strong></div>
        <div><span>Revisar</span><strong>${review}</strong></div>
        <div><span>Baixo impacto</span><strong>${low}</strong></div>
        <div><span>Principal causa</span><strong>${mainCause}</strong></div>
      </div>`;
    return true;
  }

  function enrichModal() {
    const modal = document.getElementById('cofins-auditor-v35-modal');
    if (!modal || modal.querySelector('.diagnostico-fiscal-v403__modal-meta')) return false;
    const title = modal.querySelector('.cofins-auditor-v35__header h5')?.textContent || '';
    const cst = title.match(/CST\s+([^\s/]+)/i)?.[1] || '';
    const cfop = title.match(/CFOP\s+([^\s]+)/i)?.[1] || '';
    const item = findings().find(candidate => candidate.cst === cst && candidate.cfop === cfop);
    if (!item) return false;

    const guidance = modal.querySelector('.cofins-auditor-v37__guidance');
    if (!guidance) return false;
    const meta = document.createElement('div');
    meta.className = 'diagnostico-fiscal-v403__modal-meta';
    meta.innerHTML = `
      <div><span>Prioridade</span><strong>#${item.priority}</strong></div>
      <div><span>Gravidade</span><strong class="diagnostico-fiscal-v403__badge ${badgeClass(item.severity)}">${item.severity}</strong></div>
      <div><span>Causa provável</span><strong>${item.causeType}</strong></div>
      <div><span>Confiança</span><strong>${item.confidence}</strong></div>
    `;
    guidance.prepend(meta);

    const actionRow = Array.from(guidance.querySelectorAll('.cofins-auditor-v37__guidance-row')).find(row => row.querySelector('strong')?.textContent === 'Ação sugerida');
    if (actionRow?.querySelector('span')) actionRow.querySelector('span').textContent = item.action;
    return true;
  }

  function scheduleInitialRender(attempt = 0) {
    if (renderSummary()) return;
    if (attempt >= 20) return;
    setTimeout(() => scheduleInitialRender(attempt + 1), 250);
  }

  function install() {
    scheduleInitialRender();
    document.addEventListener('omnixml:cofins-audit-ready', renderSummary);
    document.addEventListener('omnixml:cofins-pendency-updated', renderSummary);
    document.addEventListener('click', event => {
      if (!event.target.closest('[data-cofins-details]')) return;
      renderSummary();
      requestAnimationFrame(() => requestAnimationFrame(enrichModal));
    });
    window.OmniXMLDiagnosticoFiscalV403 = { findings, renderSummary, enrichModal, severity, causeType, actionFor };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
