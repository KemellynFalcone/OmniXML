(() => {
  'use strict';

  const previousText = File.prototype.text;
  const captures = new Map();
  let renderLock = false;

  const num = value => {
    const raw = String(value ?? '').trim();
    if (!raw) return 0;
    const normalized = raw.includes(',') ? raw.replace(/\./g, '').replace(',', '.') : raw;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const money = value => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const closeMoney = value => Math.abs(Number(value || 0)) < 0.005;

  function parseM210(fields, source, line) {
    const modern = fields.length > 16;
    return {
      registro: 'M210', source, line,
      cod_cont: String(fields[2] || '').trim(),
      receita_bruta: num(fields[3]),
      base_antes_ajustes: num(fields[4]),
      acresc_base: modern ? num(fields[5]) : 0,
      reducao_base: modern ? num(fields[6]) : 0,
      base_ajustada: modern ? num(fields[7]) : num(fields[4]),
      aliquota: modern ? num(fields[8]) : num(fields[5]),
      contribuicao_apurada: modern ? num(fields[11]) : num(fields[8]),
      ajuste_acrescimo: modern ? num(fields[12]) : num(fields[9]),
      ajuste_reducao: modern ? num(fields[13]) : num(fields[10]),
      diferimento: modern ? num(fields[14]) : num(fields[11]),
      diferimento_anterior: modern ? num(fields[15]) : num(fields[12]),
      contribuicao_periodo: modern ? num(fields[16]) : num(fields[13]),
    };
  }

  function parseM610(fields, source, line) {
    const modern = fields.length > 16;
    return {
      registro: 'M610', source, line,
      cod_cont: String(fields[2] || '').trim(),
      receita_bruta: num(fields[3]),
      base_antes_ajustes: num(fields[4]),
      acresc_base: modern ? num(fields[5]) : 0,
      reducao_base: modern ? num(fields[6]) : 0,
      base_ajustada: modern ? num(fields[7]) : num(fields[4]),
      aliquota: modern ? num(fields[8]) : num(fields[5]),
      contribuicao_apurada: modern ? num(fields[11]) : num(fields[8]),
      ajuste_acrescimo: modern ? num(fields[12]) : num(fields[9]),
      ajuste_reducao: modern ? num(fields[13]) : num(fields[10]),
      diferimento: modern ? num(fields[14]) : num(fields[11]),
      diferimento_anterior: modern ? num(fields[15]) : num(fields[12]),
      contribuicao_periodo: modern ? num(fields[16]) : num(fields[13]),
    };
  }

  function parseConsolidacao(fields, registro, source, line) {
    return {
      registro, source, line,
      nao_cumulativa_periodo: num(fields[2]),
      credito_periodo: num(fields[3]),
      credito_anterior: num(fields[4]),
      nao_cumulativa_devida: num(fields[5]),
      retencao_nao_cumulativa: num(fields[6]),
      outras_deducoes_nao_cumulativa: num(fields[7]),
      nao_cumulativa_recolher: num(fields[8]),
      cumulativa_periodo: num(fields[9]),
      retencao_cumulativa: num(fields[10]),
      outras_deducoes_cumulativa: num(fields[11]),
      cumulativa_recolher: num(fields[12]),
      total_recolher: num(fields[13]),
    };
  }

  function parseBlockM(text, source) {
    const result = { source, m200: null, m210: [], m600: null, m610: [] };
    let line = 0;
    for (const raw of String(text || '').split(/\r?\n/)) {
      line += 1;
      const value = raw.trim();
      if (!value.startsWith('|')) continue;
      const fields = value.split('|');
      const reg = String(fields[1] || '').trim();
      if (reg === 'M200') result.m200 = parseConsolidacao(fields, reg, source, line);
      else if (reg === 'M210') result.m210.push(parseM210(fields, source, line));
      else if (reg === 'M600') result.m600 = parseConsolidacao(fields, reg, source, line);
      else if (reg === 'M610') result.m610.push(parseM610(fields, source, line));
    }
    return result;
  }

  function aggregate() {
    const values = Array.from(captures.values());
    const m210 = values.flatMap(x => x.m210 || []);
    const m610 = values.flatMap(x => x.m610 || []);
    const m200 = values.map(x => x.m200).filter(Boolean);
    const m600 = values.map(x => x.m600).filter(Boolean);
    const sum = (rows, field) => rows.reduce((total, row) => total + Number(row?.[field] || 0), 0);
    const consolidate = rows => ({
      nao_cumulativa_periodo: sum(rows, 'nao_cumulativa_periodo'),
      credito_periodo: sum(rows, 'credito_periodo'),
      credito_anterior: sum(rows, 'credito_anterior'),
      nao_cumulativa_devida: sum(rows, 'nao_cumulativa_devida'),
      retencao_nao_cumulativa: sum(rows, 'retencao_nao_cumulativa'),
      outras_deducoes_nao_cumulativa: sum(rows, 'outras_deducoes_nao_cumulativa'),
      nao_cumulativa_recolher: sum(rows, 'nao_cumulativa_recolher'),
      cumulativa_periodo: sum(rows, 'cumulativa_periodo'),
      retencao_cumulativa: sum(rows, 'retencao_cumulativa'),
      outras_deducoes_cumulativa: sum(rows, 'outras_deducoes_cumulativa'),
      cumulativa_recolher: sum(rows, 'cumulativa_recolher'),
      total_recolher: sum(rows, 'total_recolher'),
    });
    return {
      m210, m610,
      m200: consolidate(m200),
      m600: consolidate(m600),
      total_pis_detalhado: sum(m210, 'contribuicao_periodo'),
      total_cofins_detalhado: sum(m610, 'contribuicao_periodo'),
      fontes: values.map(x => x.source),
    };
  }

  function metric(label, value, hint = '') {
    const box = document.createElement('div');
    box.className = 'bloco-m-v40__metric';
    const strong = document.createElement('strong');
    strong.textContent = label;
    const amount = document.createElement('b');
    amount.textContent = money(value);
    box.append(strong, amount);
    if (hint) {
      const small = document.createElement('small');
      small.textContent = hint;
      box.append(small);
    }
    return box;
  }

  function row(label, documental, detalhado, note) {
    const diff = Number(documental || 0) - Number(detalhado || 0);
    const tr = document.createElement('tr');
    for (const value of [label, money(documental), money(detalhado), money(diff), note]) {
      const td = document.createElement('td');
      td.textContent = value;
      tr.append(td);
    }
    if (!closeMoney(diff)) tr.children[3].className = 'bloco-m-v40__diff';
    return tr;
  }

  function reconciliationCard(title, data, taxLabel) {
    const card = document.createElement('div');
    card.className = 'bloco-m-v40__reconciliation';
    const h = document.createElement('h6');
    h.textContent = title;
    const grid = document.createElement('div');
    grid.className = 'bloco-m-v40__grid';
    grid.append(
      metric('Contribuição do período', data.nao_cumulativa_periodo + data.cumulativa_periodo, `${taxLabel} antes de créditos/deduções`),
      metric('Créditos descontados', data.credito_periodo + data.credito_anterior),
      metric('Retenções', data.retencao_nao_cumulativa + data.retencao_cumulativa),
      metric('Outras deduções', data.outras_deducoes_nao_cumulativa + data.outras_deducoes_cumulativa),
      metric('Valor a recolher', data.total_recolher, 'Consolidação final do Bloco M')
    );
    card.append(h, grid);
    return card;
  }

  function renderSignature(efd, apuracao) {
    return JSON.stringify({
      efd: {
        pis: Number(efd?.totais?.pis || 0),
        cofins: Number(efd?.totais?.cofins || 0),
        registros: Number(efd?.registros_saida_suportados || 0)
      },
      blocoM: {
        pis: Number(apuracao?.total_pis_detalhado || 0),
        cofins: Number(apuracao?.total_cofins_detalhado || 0),
        m210: apuracao?.m210?.length || 0,
        m610: apuracao?.m610?.length || 0,
        fontes: apuracao?.fontes || []
      }
    });
  }

  function render() {
    if (renderLock) return;
    const host = document.getElementById('pis-cofins-confront-v30');
    const efd = window.__omnixmlEfdContribLast;
    if (!host || !efd?.totais || !captures.size) return;

    const apuracao = aggregate();
    const signature = renderSignature(efd, apuracao);
    const existing = document.getElementById('bloco-m-v40');
    if (existing?.dataset?.renderSignature === signature) {
      window.__omnixmlBlocoMArredondamentoV401?.enhance?.();
      return;
    }

    renderLock = true;
    try {
      existing?.remove();
      const section = document.createElement('section');
      section.id = 'bloco-m-v40';
      section.className = 'bloco-m-v40';
      section.dataset.renderSignature = signature;

      const head = document.createElement('div');
      head.className = 'bloco-m-v40__head';
      const copy = document.createElement('div');
      const eyebrow = document.createElement('span');
      eyebrow.textContent = 'v40 · Bloco M';
      const title = document.createElement('h5');
      title.textContent = 'Da escrituração documental à apuração final';
      const subtitle = document.createElement('p');
      subtitle.textContent = 'Confronto entre C170/C175, detalhamento M210/M610 e consolidação M200/M600.';
      copy.append(eyebrow, title, subtitle);
      const badge = document.createElement('span');
      badge.className = 'bloco-m-v40__badge';
      badge.textContent = `${apuracao.m210.length} M210 · ${apuracao.m610.length} M610`;
      head.append(copy, badge);

      const tableWrap = document.createElement('div');
      tableWrap.className = 'bloco-m-v40__table-wrap';
      const table = document.createElement('table');
      const thead = document.createElement('thead');
      const hr = document.createElement('tr');
      ['Tributo', 'C170/C175', 'M210/M610', 'Diferença', 'Leitura'].forEach(x => {
        const th = document.createElement('th'); th.textContent = x; hr.append(th);
      });
      thead.append(hr);
      const tbody = document.createElement('tbody');
      const pisDiff = Number(efd.totais.pis || 0) - apuracao.total_pis_detalhado;
      const cofinsDiff = Number(efd.totais.cofins || 0) - apuracao.total_cofins_detalhado;
      tbody.append(
        row('PIS', efd.totais.pis, apuracao.total_pis_detalhado, closeMoney(pisDiff) ? 'Escrituração documental conciliada com M210.' : 'Revisar outros blocos, ajustes ou composição da apuração do PIS.'),
        row('COFINS', efd.totais.cofins, apuracao.total_cofins_detalhado, closeMoney(cofinsDiff) ? 'Escrituração documental conciliada com M610.' : 'Revisar outros blocos, ajustes ou composição da apuração da COFINS.')
      );
      table.append(thead, tbody);
      tableWrap.append(table);

      const warning = document.createElement('div');
      warning.className = 'bloco-m-v40__note';
      warning.textContent = 'A diferença entre C170/C175 e M210/M610 não é automaticamente um erro: o Bloco M pode consolidar valores oriundos de outros blocos da EFD-Contribuições e ajustes de apuração. O OmniXML sinaliza a diferença para investigação, sem sugerir alteração automática.';

      section.append(head, tableWrap);
      if (apuracao.m200.total_recolher || apuracao.m200.nao_cumulativa_periodo || apuracao.m200.cumulativa_periodo) {
        section.append(reconciliationCard('PIS — M200', apuracao.m200, 'PIS'));
      }
      if (apuracao.m600.total_recolher || apuracao.m600.nao_cumulativa_periodo || apuracao.m600.cumulativa_periodo) {
        section.append(reconciliationCard('COFINS — M600', apuracao.m600, 'COFINS'));
      }
      section.append(warning);
      host.append(section);

      queueMicrotask(() => window.__omnixmlBlocoMArredondamentoV401?.enhance?.());
    } finally {
      renderLock = false;
    }
  }

  File.prototype.text = async function(...args) {
    const value = await previousText.apply(this, args);
    if (/\.txt$/i.test(this.name || '') && /\|M(?:200|210|600|610)\|/.test(value)) {
      const source = this.webkitRelativePath || this.name || 'EFD-Contribuições';
      captures.set(source, parseBlockM(value, source));
      queueMicrotask(render);
    }
    return value;
  };

  const observer = new MutationObserver(records => {
    const relevant = records.some(record => Array.from(record.addedNodes || []).some(node =>
      node?.nodeType === Node.ELEMENT_NODE && (
        node.id === 'pis-cofins-confront-v30' ||
        node.querySelector?.('#pis-cofins-confront-v30')
      )
    ));
    if (relevant) queueMicrotask(render);
  });

  const start = () => {
    observer.observe(document.documentElement, { childList: true, subtree: true });
    window.__omnixmlBlocoMV40 = { version: 40, parseBlockM, snapshot: aggregate, render };
    render();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();