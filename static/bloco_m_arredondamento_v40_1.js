(() => {
  'use strict';

  const closeMoney = value => Math.abs(Number(value || 0)) < 0.005;
  const money = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const round2 = value => Math.round((Number(value || 0) + Number.EPSILON) * 100) / 100;

  function hasApurationAdjustments(rows) {
    return (rows || []).some(row => [
      'ajuste_acrescimo', 'ajuste_reducao', 'diferimento', 'diferimento_anterior'
    ].some(field => !closeMoney(row?.[field])));
  }

  function blockMMatchesConsolidatedCalculation(rows) {
    const relevant = (rows || []).filter(row => Number(row?.base_ajustada || 0) || Number(row?.contribuicao_periodo || 0));
    if (!relevant.length || hasApurationAdjustments(relevant)) return false;
    return relevant.every(row => {
      const calculated = round2(Number(row.base_ajustada || 0) * Number(row.aliquota || 0) / 100);
      return closeMoney(calculated - Number(row.contribuicao_periodo || 0));
    });
  }

  function documentaryItemCount(tax) {
    const rows = window.__omnixmlEfdContribLast?.detalhes || [];
    const valueField = tax === 'PIS' ? 'valor_pis' : 'valor_cofins';
    const baseField = tax === 'PIS' ? 'base_pis' : 'base_cofins';
    return rows.filter(row => Number(row?.[valueField] || 0) || Number(row?.[baseField] || 0)).length;
  }

  function roundingTolerance(itemCount) {
    return Math.max(0.005, Number(itemCount || 0) * 0.005 + 0.005);
  }

  function roundingDiagnosis(tax, documental, blocoM, detailRows) {
    const diff = Number(documental || 0) - Number(blocoM || 0);
    if (closeMoney(diff)) {
      return {
        kind: 'conciliado',
        text: `Escrituração documental conciliada com ${tax === 'PIS' ? 'M210' : 'M610'}.`
      };
    }

    const items = documentaryItemCount(tax);
    const formulaMatches = blockMMatchesConsolidatedCalculation(detailRows);
    const plausibleByItems = items > 0 && Math.abs(diff) <= roundingTolerance(items);

    if (formulaMatches && plausibleByItems) {
      return {
        kind: 'arredondamento',
        text: `Provável diferença de arredondamento (${money(Math.abs(diff))}). O C170/C175 soma valores calculados por item, enquanto o Bloco M calcula a contribuição sobre a base consolidada. Validar antes de tratar como divergência fiscal.`
      };
    }

    return {
      kind: 'investigar',
      text: `Diferença de ${money(Math.abs(diff))}. Revisar outros blocos, ajustes e composição da apuração antes de concluir que existe erro fiscal.`
    };
  }

  function addExplanation(section, results) {
    let note = document.getElementById('bloco-m-v40-1-rounding-note');
    const rounding = results.filter(result => result.kind === 'arredondamento');
    if (!rounding.length) {
      note?.remove();
      return;
    }
    if (!note) {
      note = document.createElement('div');
      note.id = 'bloco-m-v40-1-rounding-note';
      note.style.cssText = 'margin:12px 0;padding:12px 14px;border:1px solid #fde68a;border-radius:10px;background:#fffbeb;color:#78350f;font-size:12px;line-height:1.5';
      section.querySelector('.bloco-m-v40__table-wrap')?.after(note);
    }
    note.innerHTML = '<strong>v40.1 · Provável arredondamento</strong><br>Diferenças pequenas podem surgir porque os documentos acumulam arredondamentos por item, enquanto M210/M610 calculam a contribuição sobre a base consolidada. O OmniXML mantém a diferença visível, mas não a classifica automaticamente como erro fiscal.';
  }

  function enhance() {
    const section = document.getElementById('bloco-m-v40');
    const efd = window.__omnixmlEfdContribLast;
    const api = window.__omnixmlBlocoMV40;
    if (!section || !efd?.totais || typeof api?.snapshot !== 'function') return;

    const snapshot = api.snapshot();
    const rows = Array.from(section.querySelectorAll('tbody tr'));
    if (rows.length < 2) return;

    const pis = roundingDiagnosis('PIS', efd.totais.pis, snapshot.total_pis_detalhado, snapshot.m210 || []);
    const cofins = roundingDiagnosis('COFINS', efd.totais.cofins, snapshot.total_cofins_detalhado, snapshot.m610 || []);

    [[rows[0], pis], [rows[1], cofins]].forEach(([tr, result]) => {
      const reading = tr?.children?.[4];
      const diff = tr?.children?.[3];
      if (!reading) return;
      reading.textContent = result.text;
      reading.dataset.v401Diagnosis = result.kind;
      if (result.kind === 'arredondamento') {
        reading.style.fontWeight = '700';
        reading.style.color = '#92400e';
        if (diff) {
          diff.style.background = '#fffbeb';
          diff.style.color = '#92400e';
        }
      } else {
        reading.style.fontWeight = '';
        reading.style.color = '';
      }
    });

    addExplanation(section, [pis, cofins]);
    window.__omnixmlBlocoMArredondamentoV401 = {
      version: '40.1',
      roundingDiagnosis,
      roundingTolerance,
      blockMMatchesConsolidatedCalculation,
      enhance
    };
  }

  const observer = new MutationObserver(() => queueMicrotask(enhance));
  const start = () => {
    observer.observe(document.documentElement, { childList: true, subtree: true });
    enhance();
    window.__omnixmlBlocoMArredondamentoV401 = {
      version: '40.1',
      roundingDiagnosis,
      roundingTolerance,
      blockMMatchesConsolidatedCalculation,
      enhance
    };
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
