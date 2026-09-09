(() => {
  'use strict';

  let input = null;

  const brNumber = value => {
    const raw = String(value ?? '').trim();
    if (!raw) return 0;
    const normalized = raw.includes(',') ? raw.replace(/\./g, '').replace(',', '.') : raw;
    const number = Number(normalized);
    return Number.isFinite(number) ? number : 0;
  };

  const money = value => Number(value || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });

  function setStatus(text, kind = 'indigo') {
    const el = document.getElementById('statusAuditoria');
    if (!el) return;
    el.replaceChildren();
    const dot = document.createElement('span');
    dot.className = `w-2 h-2 rounded-full ${kind === 'emerald' ? 'bg-emerald-500' : kind === 'red' ? 'bg-red-500' : 'bg-indigo-500 animate-pulse'}`;
    el.append(dot, document.createTextNode(` ${text}`));
  }

  function parseC170(fields, source, lineNumber) {
    const cstPis = String(fields[25] || '').trim().padStart(2, '0');
    if (!cstPis || cstPis === '00') return null;
    const gross = brNumber(fields[7]);
    const discount = brNumber(fields[8]);
    return {
      source,
      line: lineNumber,
      registro: 'C170',
      cst: cstPis,
      cfop: String(fields[11] || '').trim(),
      receita: Math.max(0, gross - discount),
      base_pis: brNumber(fields[26]),
      valor_pis: brNumber(fields[30]),
      cst_cofins: String(fields[31] || '').trim().padStart(2, '0'),
      base_cofins: brNumber(fields[32]),
      valor_cofins: brNumber(fields[36])
    };
  }

  function parseC175(fields, source, lineNumber) {
    const cstPis = String(fields[5] || '').trim().padStart(2, '0');
    if (!cstPis || cstPis === '00') return null;
    return {
      source,
      line: lineNumber,
      registro: 'C175',
      cst: cstPis,
      cfop: String(fields[2] || '').trim(),
      receita: brNumber(fields[3]),
      base_pis: brNumber(fields[6]),
      valor_pis: brNumber(fields[10]),
      cst_cofins: String(fields[11] || '').trim().padStart(2, '0'),
      base_cofins: brNumber(fields[12]),
      valor_cofins: brNumber(fields[16])
    };
  }

  function parseEfdContribText(text, source) {
    const rows = [];
    let has0000 = false;
    let currentC100Oper = null;
    let c170Count = 0;
    let c175Count = 0;
    let lineNumber = 0;

    for (const rawLine of String(text || '').split(/\r?\n/)) {
      lineNumber += 1;
      const line = rawLine.trim();
      if (!line || line[0] !== '|') continue;
      const fields = line.split('|');
      const reg = fields[1] || '';

      if (reg === '0000') has0000 = true;
      if (reg === 'C100') {
        currentC100Oper = String(fields[2] || '').trim();
        continue;
      }

      if (reg === 'C170') {
        c170Count += 1;
        if (currentC100Oper !== '1') continue;
        const row = parseC170(fields, source, lineNumber);
        if (row) rows.push(row);
        continue;
      }

      if (reg === 'C175') {
        c175Count += 1;
        if (currentC100Oper !== '1') continue;
        const row = parseC175(fields, source, lineNumber);
        if (row) rows.push(row);
      }
    }

    if (!has0000) throw new Error(`O arquivo ${source} não parece ser uma EFD-Contribuições válida (registro 0000 não encontrado).`);
    return { rows, c170Count, c175Count };
  }

  function aggregate(rows) {
    const byCst = new Map();
    for (const row of rows) {
      const current = byCst.get(row.cst) || {
        cst: row.cst,
        vl_opr: 0,
        vl_pis: 0,
        vl_cofins: 0,
        vl_bc_pis: 0,
        vl_bc_cofins: 0,
        registros: 0
      };
      current.vl_opr += row.receita;
      current.vl_pis += row.valor_pis;
      current.vl_cofins += row.valor_cofins;
      current.vl_bc_pis += row.base_pis;
      current.vl_bc_cofins += row.base_cofins;
      current.registros += 1;
      byCst.set(row.cst, current);
    }

    const csts = Array.from(byCst.values()).sort((a, b) => b.vl_opr - a.vl_opr || a.cst.localeCompare(b.cst));
    return {
      total_receita: csts.reduce((total, item) => total + item.vl_opr, 0),
      total_pis: csts.reduce((total, item) => total + item.vl_pis, 0),
      total_cofins: csts.reduce((total, item) => total + item.vl_cofins, 0),
      csts
    };
  }

  function metric(title, xmlValue, spedValue) {
    const diff = Number(xmlValue || 0) - Number(spedValue || 0);
    const box = document.createElement('div');
    box.className = 'pis-confront-v30__metric';
    const label = document.createElement('strong');
    label.textContent = title;
    const values = document.createElement('div');
    values.className = 'pis-confront-v30__values';

    for (const [name, value, kind] of [
      ['XMLs', xmlValue, ''],
      ['EFD', spedValue, ''],
      ['Diferença', diff, Math.abs(diff) < 0.005 ? 'ok' : 'diff']
    ]) {
      const item = document.createElement('span');
      if (kind) item.className = kind;
      item.append(document.createTextNode(name));
      const amount = document.createElement('b');
      amount.textContent = money(value);
      item.append(amount);
      values.append(item);
    }

    box.append(label, values);
    return { box, diff };
  }

  function renderConfront(summary) {
    let section = document.getElementById('pis-cofins-confront-v30');
    if (section) section.remove();
    section = document.createElement('section');
    section.id = 'pis-cofins-confront-v30';
    section.className = 'pis-confront-v30';

    const xml = window.__omnixmlXmlPisCofins?.snapshot?.();
    if (!xml || !xml.notas_saida) {
      const empty = document.createElement('div');
      empty.className = 'pis-confront-v30__empty';
      empty.textContent = 'A EFD-Contribuições foi processada. Para confrontar com os XMLs, importe e audite primeiro os XMLs da mesma empresa e do mesmo período.';
      section.append(empty);
      document.getElementById('res-pis-cofins')?.prepend(section);
      return { disponivel: false };
    }

    const head = document.createElement('div');
    head.className = 'pis-confront-v30__head';
    const copy = document.createElement('div');
    const title = document.createElement('h4');
    title.textContent = 'Confronto documental: XMLs × EFD-Contribuições';
    const subtitle = document.createElement('p');
    subtitle.textContent = 'Receitas e contribuições dos documentos fiscais comparadas com C170/C175.';
    copy.append(title, subtitle);
    const badge = document.createElement('span');
    badge.className = 'pis-confront-v30__badge';
    badge.textContent = `${xml.notas_saida} notas de saída`;
    head.append(copy, badge);

    const grid = document.createElement('div');
    grid.className = 'pis-confront-v30__grid';
    const receita = metric('Receita documental', xml.totais.receita, summary.total_receita);
    const pis = metric('PIS documental', xml.totais.pis, summary.total_pis);
    const cofins = metric('COFINS documental', xml.totais.cofins, summary.total_cofins);
    grid.append(receita.box, pis.box, cofins.box);

    const tableWrap = document.createElement('div');
    tableWrap.className = 'pis-confront-v30__table-wrap';
    const table = document.createElement('table');
    table.className = 'pis-confront-v30__table';
    const thead = document.createElement('thead');
    const header = document.createElement('tr');
    for (const label of ['CST PIS', 'Receita XML', 'Receita EFD', 'Diferença', 'PIS XML', 'PIS EFD']) {
      const th = document.createElement('th');
      th.textContent = label;
      header.append(th);
    }
    thead.append(header);
    const tbody = document.createElement('tbody');
    const xmlByCst = new Map((xml.csts || []).map(row => [row.cst, row]));
    const efdByCst = new Map((summary.csts || []).map(row => [row.cst, row]));
    const allCsts = Array.from(new Set([...xmlByCst.keys(), ...efdByCst.keys()])).sort();
    for (const cst of allCsts) {
      const xr = xmlByCst.get(cst) || {};
      const er = efdByCst.get(cst) || {};
      const row = document.createElement('tr');
      const values = [
        cst,
        money(xr.vl_opr),
        money(er.vl_opr),
        money(Number(xr.vl_opr || 0) - Number(er.vl_opr || 0)),
        money(xr.vl_pis),
        money(er.vl_pis)
      ];
      for (const value of values) {
        const td = document.createElement('td');
        td.textContent = value;
        row.append(td);
      }
      tbody.append(row);
    }
    table.append(thead, tbody);
    tableWrap.append(table);

    const note = document.createElement('p');
    note.className = 'pis-confront-v30__note';
    note.textContent = 'Este confronto é documental e usa os valores presentes nos XMLs e nos registros C170/C175. A apuração final do PIS/COFINS deve ser validada separadamente contra o Bloco M (M200/M210 e M600/M610), pois pode conter créditos, ajustes e outros componentes.';

    section.append(head, grid, tableWrap, note);
    document.getElementById('res-pis-cofins')?.prepend(section);
    return {
      disponivel: true,
      xml: xml.totais,
      efd: { receita: summary.total_receita, pis: summary.total_pis, cofins: summary.total_cofins },
      diferencas: { receita: receita.diff, pis: pis.diff, cofins: cofins.diff }
    };
  }

  function renderResult(summary) {
    const total = document.getElementById('total-receita-pis');
    if (total) total.textContent = money(summary.total_receita);
    if (window.dtPisCofins?.clear) window.dtPisCofins.clear().rows.add(summary.csts).draw();
    document.getElementById('res-pis-cofins')?.classList.remove('hidden');
    return renderConfront(summary);
  }

  async function processFiles(fileList) {
    const files = Array.from(fileList || []).filter(file => /\.txt$/i.test(file.name));
    if (!files.length) return;

    setStatus(`Lendo ${files.length} arquivo(s) EFD-Contribuições localmente...`);
    const rows = [];
    const seen = new Set();
    let rawC170 = 0;
    let rawC175 = 0;

    try {
      for (const file of files) {
        const source = file.webkitRelativePath || file.name;
        const parsed = parseEfdContribText(await file.text(), source);
        rawC170 += parsed.c170Count;
        rawC175 += parsed.c175Count;
        for (const row of parsed.rows) {
          const key = `${row.source}|${row.line}|${row.registro}|${row.cst}|${row.cfop}|${row.receita}|${row.valor_pis}|${row.valor_cofins}`;
          if (seen.has(key)) continue;
          seen.add(key);
          rows.push(row);
        }
      }

      if (rawC170 === 0 && rawC175 === 0) {
        throw new Error('Nenhum registro C170 ou C175 foi encontrado nos arquivos selecionados.');
      }

      const summary = aggregate(rows);
      const confronto = renderResult(summary);
      setStatus(`EFD-Contribuições processada localmente: ${files.length} arquivo(s), ${rows.length} registro(s) de saída suportado(s)`, 'emerald');
      window.__omnixmlEfdContribLast = {
        version: 30,
        files: files.map(file => file.webkitRelativePath || file.name),
        registros_lidos: { c170: rawC170, c175: rawC175 },
        registros_saida_suportados: rows.length,
        totais: {
          receita: summary.total_receita,
          pis: summary.total_pis,
          cofins: summary.total_cofins
        },
        confronto,
        csts: summary.csts.map(item => ({ ...item })),
        detalhes: rows.map(row => ({ ...row }))
      };
    } catch (error) {
      console.error(error);
      setStatus('Falha ao processar a EFD-Contribuições', 'red');
      alert(error?.message || 'Falha ao processar a EFD-Contribuições.');
    } finally {
      if (input) input.value = '';
    }
  }

  function install() {
    input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt,text/plain';
    input.multiple = true;
    input.className = 'hidden';
    input.id = 'omnixml-efd-contrib-local-input-v29';
    input.addEventListener('change', event => processFiles(event.target.files));
    document.body.appendChild(input);

    window.importarPisCofins = () => input.click();
    window.__omnixmlEfdContribLocal = {
      version: 30,
      parseEfdContribText,
      aggregate,
      renderConfront
    };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
