(() => {
  const original = window.atualizarPainelDinamico;
  if (typeof original !== 'function') return;

  const numero = value => {
    const n = Number.parseInt(String(value ?? '').replace(/\D/g, ''), 10);
    return Number.isFinite(n) ? n : null;
  };
  const modeloNota = nota => {
    const tipo = String(nota?.tipo || '');
    if (tipo.includes('NFC-e')) return 'NFC-e';
    if (tipo.includes('NF-e')) return 'NF-e';
    return tipo || 'Documento';
  };
  const codigoModelo = modelo => modelo === 'NFC-e' ? '65' : modelo === 'NF-e' ? '55' : '';
  const node = (tag, className = '', text = '') => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== '') el.textContent = String(text);
    return el;
  };

  function detectarLacunas(notas, inutilizacoes) {
    const grupos = new Map();
    for (const nota of notas || []) {
      if (String(nota?.operacao || '').trim() !== 'Saída') continue;
      const n = numero(nota.numero_nota || nota.numero);
      if (n == null) continue;
      const modelo = modeloNota(nota);
      const serie = String(nota.serie || 'N/A');
      const chave = `${modelo}|${serie}`;
      if (!grupos.has(chave)) grupos.set(chave, { modelo, serie, numeros: new Set() });
      grupos.get(chave).numeros.add(n);
    }

    const resultado = [];
    for (const grupo of grupos.values()) {
      const nums = Array.from(grupo.numeros).sort((a, b) => a - b);
      if (nums.length < 2) continue;
      const inicial = nums[0], final = nums[nums.length - 1];
      const candidatas = [];
      for (let n = inicial; n <= final; n++) if (!grupo.numeros.has(n)) candidatas.push(n);
      if (!candidatas.length) continue;

      const faixas = (inutilizacoes || []).filter(i =>
        i?.homologada && String(i.modelo) === codigoModelo(grupo.modelo) && String(i.serie) === grupo.serie
      );
      const inutilizadas = [], conferir = [];
      for (const n of candidatas) {
        const faixa = faixas.find(i => n >= Number(i.inicial) && n <= Number(i.final));
        if (faixa) inutilizadas.push({ numero: n, protocolo: faixa.protocolo || '', arquivo: faixa.arquivo || '' });
        else conferir.push(n);
      }
      resultado.push({ modelo: grupo.modelo, serie: grupo.serie, inicial, final, inutilizadas, conferir });
    }
    return resultado;
  }

  function card(label, id, boxClass, valueClass) {
    const box = node('div', `rounded-lg ${boxClass} p-3`);
    box.appendChild(node('div', `text-[11px] uppercase font-bold ${valueClass.replace('text-xl font-black ', '')}`, label));
    const value = node('div', valueClass, '0');
    value.id = id;
    box.appendChild(value);
    return box;
  }

  function garantirPainel() {
    if (document.getElementById('omnixml-diagnostico-v2')) return;
    const tab = document.getElementById('tab-resumo');
    const resumo = document.getElementById('faixa-resumo-auditoria');
    if (!tab) return;

    const sec = node('section', 'hidden mb-5');
    sec.id = 'omnixml-diagnostico-v2';

    const toggle = node('button', 'w-full rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm flex items-center justify-between gap-4 hover:bg-slate-50 transition-colors text-left');
    toggle.id = 'omnixml-diag-toggle';
    toggle.type = 'button';

    const left = node('div', 'flex items-center gap-3 min-w-0');
    left.appendChild(node('span', 'w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold', '✓'));
    const titleWrap = node('div', 'min-w-0');
    titleWrap.appendChild(node('div', 'font-bold text-slate-800', 'Diagnóstico do fechamento'));
    const summary = node('div', 'text-sm text-slate-500 truncate', 'Verificações adicionais disponíveis');
    summary.id = 'omnixml-diag-resumo';
    titleWrap.appendChild(summary);
    left.appendChild(titleWrap);
    toggle.appendChild(left);

    const right = node('div', 'flex items-center gap-3 shrink-0');
    const status = node('span', 'px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 text-slate-600', 'VER DETALHES');
    status.id = 'omnixml-diag-status';
    const seta = node('span', 'text-slate-400', '⌄');
    seta.id = 'omnixml-diag-seta';
    right.append(status, seta);
    toggle.appendChild(right);
    sec.appendChild(toggle);

    const conteudo = node('div', 'hidden mt-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm');
    conteudo.id = 'omnixml-diag-conteudo';
    const grid = node('div', 'grid grid-cols-2 md:grid-cols-5 gap-3 mb-4');
    grid.append(
      card('Falhas fiscais', 'diag-falhas-v2', 'bg-rose-50', 'text-xl font-black text-rose-700'),
      card('A conferir', 'diag-lacunas-v2', 'bg-amber-50', 'text-xl font-black text-amber-700'),
      card('Inutilizadas', 'diag-inutil-v2', 'bg-blue-50', 'text-xl font-black text-blue-700'),
      card('Duplicidades', 'diag-dup-v2', 'bg-orange-50', 'text-xl font-black text-orange-700'),
      card('Alertas tributários', 'diag-trib-v2', 'bg-violet-50', 'text-xl font-black text-violet-700')
    );
    conteudo.appendChild(grid);

    const exp = node('div', 'text-sm text-slate-600 mb-4');
    exp.id = 'omnixml-diag-explicacao';
    conteudo.appendChild(exp);

    const box = node('div', 'hidden overflow-x-auto rounded-lg border border-slate-200');
    box.id = 'omnixml-lacunas-v2';
    const table = node('table', 'w-full text-sm text-left');
    const thead = node('thead', 'bg-slate-50 text-xs uppercase text-slate-500');
    const trh = node('tr');
    for (const label of ['Modelo', 'Série', 'Inicial', 'Final', 'Inutilizadas', 'A conferir']) {
      trh.appendChild(node('th', 'p-3', label));
    }
    thead.appendChild(trh);
    const tbody = node('tbody');
    tbody.id = 'omnixml-lacunas-v2-body';
    table.append(thead, tbody);
    box.appendChild(table);
    conteudo.appendChild(box);

    conteudo.appendChild(node(
      'p',
      'mt-4 text-xs text-slate-400',
      'Canceladas continuam ocupando a numeração porque o XML da nota existe. Inutilizações homologadas (cStat 102) justificam números sem NF-e/NFC-e. Só números sem nota e sem inutilização homologada ficam em “A conferir”.'
    ));
    sec.appendChild(conteudo);

    if (resumo && resumo.parentElement === tab) resumo.insertAdjacentElement('afterend', sec);
    else tab.prepend(sec);

    toggle.addEventListener('click', () => {
      const abrir = conteudo.classList.contains('hidden');
      conteudo.classList.toggle('hidden', !abrir);
      seta.textContent = abrir ? '⌃' : '⌄';
    });
  }

  function appendCell(row, text, className = 'p-3') {
    const cell = node('td', className);
    cell.textContent = String(text ?? '');
    row.appendChild(cell);
  }

  function renderizarLinhas(body, grupos) {
    body.replaceChildren();
    for (const g of grupos) {
      const row = node('tr', 'border-t border-slate-100');
      appendCell(row, g.modelo, 'p-3 font-semibold');
      appendCell(row, g.serie, 'p-3 font-mono');
      appendCell(row, g.inicial, 'p-3 font-mono');
      appendCell(row, g.final, 'p-3 font-mono');
      appendCell(row, g.inutilizadas.length ? g.inutilizadas.map(x => x.numero).join(', ') : '—', 'p-3 font-mono text-blue-700');
      appendCell(
        row,
        g.conferir.length ? g.conferir.join(', ') : 'Nenhum ✓',
        `p-3 font-mono ${g.conferir.length ? 'text-amber-700' : 'text-emerald-700'}`
      );
      body.appendChild(row);
    }
  }

  function renderizar(dados) {
    garantirPainel();
    const sec = document.getElementById('omnixml-diagnostico-v2');
    if (!sec) return;
    sec.classList.remove('hidden');

    const notas = dados?.notas || [];
    const inutilizacoes = window.__omnixmlInutilizacoes || [];
    const grupos = detectarLacunas(notas, inutilizacoes);
    const qtdConferir = grupos.reduce((s, g) => s + g.conferir.length, 0);
    const qtdInutilizadas = grupos.reduce((s, g) => s + g.inutilizadas.length, 0);
    const falhas = Number(dados?.total_erros || (dados?.erros || []).length || 0);
    const duplicidades = Number((dados?.duplicidades || []).length || 0);
    const alertasTrib = (dados?.auditoria || []).filter(a => !['OK', 'Válido'].includes(String(a.status || ''))).length;
    const set = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = Number(value).toLocaleString('pt-BR');
    };
    set('diag-falhas-v2', falhas);
    set('diag-lacunas-v2', qtdConferir);
    set('diag-inutil-v2', qtdInutilizadas);
    set('diag-dup-v2', duplicidades);
    set('diag-trib-v2', alertasTrib);

    const partes = [];
    if (falhas) partes.push(`${falhas} falha${falhas === 1 ? '' : 's'} fiscal${falhas === 1 ? '' : 'is'}`);
    if (qtdInutilizadas) partes.push(`${qtdInutilizadas} inutilizaç${qtdInutilizadas === 1 ? 'ão' : 'ões'} justificada${qtdInutilizadas === 1 ? '' : 's'}`);
    if (qtdConferir) partes.push(`${qtdConferir} número${qtdConferir === 1 ? '' : 's'} a conferir`);
    if (duplicidades) partes.push(`${duplicidades} duplicidade${duplicidades === 1 ? '' : 's'}`);
    if (alertasTrib) partes.push(`${alertasTrib} alerta${alertasTrib === 1 ? '' : 's'} tributário${alertasTrib === 1 ? '' : 's'}`);
    const resumo = document.getElementById('omnixml-diag-resumo');
    if (resumo) resumo.textContent = partes.length ? partes.join(' • ') : 'Nenhuma pendência adicional detectada';

    const status = document.getElementById('omnixml-diag-status');
    if (status) {
      if (falhas || duplicidades) {
        status.textContent = 'REVISAR';
        status.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-100 text-rose-700';
      } else if (qtdConferir || alertasTrib) {
        status.textContent = 'CONFERIR';
        status.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-100 text-amber-700';
      } else {
        status.textContent = 'OK';
        status.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-700';
      }
    }

    const exp = document.getElementById('omnixml-diag-explicacao');
    if (exp) {
      exp.replaceChildren();
      const strong1 = node('strong', '', 'O que isto faz?');
      const strong2 = node('strong', '', 'Saídas');
      exp.append(strong1, document.createTextNode(' Confere somente a sequência de '), strong2,
        document.createTextNode(' da empresa. Números ocupados por notas canceladas continuam existentes. Quando falta uma nota, o OmniXML procura uma inutilização homologada na pasta e só mantém como pendência o número sem justificativa.'));
    }

    const box = document.getElementById('omnixml-lacunas-v2');
    const body = document.getElementById('omnixml-lacunas-v2-body');
    if (box && body) {
      if (grupos.length) {
        box.classList.remove('hidden');
        renderizarLinhas(body, grupos);
      } else {
        box.classList.add('hidden');
        body.replaceChildren();
      }
    }
  }

  window.atualizarPainelDinamico = function(dados) {
    const retorno = original.apply(this, arguments);
    try { renderizar(dados || {}); }
    catch (err) { console.error('OmniXML diagnóstico v2:', err); }
    return retorno;
  };

  document.addEventListener('DOMContentLoaded', garantirPainel);
})();
