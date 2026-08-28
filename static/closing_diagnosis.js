(() => {
  const original = window.atualizarPainelDinamico;
  if (typeof original !== 'function') return;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const numero = value => {
    const n = Number.parseInt(String(value ?? '').replace(/\D/g, ''), 10);
    return Number.isFinite(n) ? n : null;
  };

  function modeloNota(nota) {
    const tipo = String(nota?.tipo || '');
    if (tipo.includes('NFC-e')) return 'NFC-e';
    if (tipo.includes('NF-e')) return 'NF-e';
    return tipo || 'Documento';
  }

  function detectarLacunas(notas) {
    const grupos = new Map();
    for (const nota of notas || []) {
      const n = numero(nota.numero_nota || nota.numero);
      if (n == null) continue;
      const modelo = modeloNota(nota);
      const serie = String(nota.serie || 'N/A');
      const chave = `${modelo}|${serie}`;
      if (!grupos.has(chave)) grupos.set(chave, { modelo, serie, numeros: new Set() });
      grupos.get(chave).numeros.add(n);
    }

    const lacunas = [];
    for (const grupo of grupos.values()) {
      const nums = Array.from(grupo.numeros).sort((a, b) => a - b);
      if (nums.length < 2) continue;
      for (let i = 1; i < nums.length; i++) {
        const anterior = nums[i - 1];
        const atual = nums[i];
        const qtd = atual - anterior - 1;
        if (qtd <= 0) continue;
        // Evita materializar milhares de números em caso de base parcial ou séries descontínuas.
        const amostra = [];
        const limite = Math.min(qtd, 30);
        for (let x = 1; x <= limite; x++) amostra.push(anterior + x);
        lacunas.push({
          modelo: grupo.modelo,
          serie: grupo.serie,
          de: anterior + 1,
          ate: atual - 1,
          quantidade: qtd,
          amostra,
          truncada: qtd > limite
        });
      }
    }
    return lacunas;
  }

  function garantirPainel() {
    if (document.getElementById('omnixml-diagnostico-fechamento')) return;
    const resumo = document.getElementById('faixa-resumo-auditoria');
    const tab = document.getElementById('tab-resumo');
    if (!tab) return;

    const painel = document.createElement('section');
    painel.id = 'omnixml-diagnostico-fechamento';
    painel.className = 'hidden mb-6 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden';
    painel.innerHTML = `
      <div class="p-5 md:p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600">✓</span>
            <div>
              <h3 class="text-lg font-black text-slate-800">Diagnóstico do Fechamento</h3>
              <p class="text-sm text-slate-500">Pendências encontradas antes do envio à contabilidade.</p>
            </div>
          </div>
        </div>
        <div id="omnixml-diagnostico-status" class="px-4 py-2 rounded-xl text-sm font-bold bg-slate-100 text-slate-600">Aguardando auditoria</div>
      </div>
      <div class="p-5 md:p-6">
        <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
          <div class="rounded-xl bg-rose-50 border border-rose-100 p-4"><div class="text-xs uppercase font-bold text-rose-500">XMLs com falha</div><div id="diag-falhas" class="text-2xl font-black text-rose-700 mt-1">0</div></div>
          <div class="rounded-xl bg-amber-50 border border-amber-100 p-4"><div class="text-xs uppercase font-bold text-amber-600">Lacunas numéricas</div><div id="diag-lacunas" class="text-2xl font-black text-amber-700 mt-1">0</div></div>
          <div class="rounded-xl bg-orange-50 border border-orange-100 p-4"><div class="text-xs uppercase font-bold text-orange-600">Duplicidades</div><div id="diag-duplicidades" class="text-2xl font-black text-orange-700 mt-1">0</div></div>
          <div class="rounded-xl bg-blue-50 border border-blue-100 p-4"><div class="text-xs uppercase font-bold text-blue-600">Não classificadas</div><div id="diag-nao-class" class="text-2xl font-black text-blue-700 mt-1">0</div></div>
          <div class="rounded-xl bg-violet-50 border border-violet-100 p-4"><div class="text-xs uppercase font-bold text-violet-600">Alertas tributários</div><div id="diag-tributarios" class="text-2xl font-black text-violet-700 mt-1">0</div></div>
        </div>
        <div id="omnixml-diagnostico-lista" class="space-y-2"></div>
        <div id="omnixml-lacunas-detalhes" class="hidden mt-5 overflow-x-auto rounded-xl border border-slate-200">
          <table class="w-full text-sm text-left">
            <thead class="bg-slate-50 text-xs uppercase text-slate-500"><tr><th class="p-3">Modelo</th><th class="p-3">Série</th><th class="p-3">Faixa ausente</th><th class="p-3">Qtd.</th><th class="p-3">Números</th></tr></thead>
            <tbody id="omnixml-lacunas-body"></tbody>
          </table>
        </div>
        <p class="mt-4 text-xs text-slate-400">Lacunas indicam números ausentes dentro da sequência carregada. Elas podem ser justificadas por inutilização ou por documentos que não estejam na pasta e devem ser conferidas antes do fechamento.</p>
      </div>`;

    if (resumo && resumo.parentElement === tab) resumo.insertAdjacentElement('afterend', painel);
    else tab.prepend(painel);
  }

  function item(tipo, titulo, texto, aba) {
    const cores = tipo === 'critico' ? 'border-rose-200 bg-rose-50 text-rose-800' : tipo === 'atencao' ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800';
    const botao = aba ? `<button type="button" data-diag-aba="${esc(aba)}" class="ml-auto text-xs font-bold underline underline-offset-2">Ver detalhes</button>` : '';
    return `<div class="flex items-start gap-3 border rounded-xl px-4 py-3 ${cores}"><span class="mt-0.5">${tipo === 'critico' ? '●' : tipo === 'atencao' ? '▲' : '✓'}</span><div><div class="font-bold text-sm">${esc(titulo)}</div><div class="text-xs mt-0.5 opacity-80">${esc(texto)}</div></div>${botao}</div>`;
  }

  function abrirAba(id) {
    const botaoPorAba = {
      'tab-erros': Array.from(document.querySelectorAll('.tab-btn')).find(b => /Arquivos com Erro/i.test(b.textContent || '')),
      'tab-auditoria': Array.from(document.querySelectorAll('.tab-btn')).find(b => /Validação Cruzada/i.test(b.textContent || '')),
      'tab-nfe': document.getElementById('btn-tab-nfe')
    };
    if (typeof window.mudarAba === 'function') window.mudarAba(id, botaoPorAba[id] || null);
  }

  function renderizar(dados) {
    garantirPainel();
    const painel = document.getElementById('omnixml-diagnostico-fechamento');
    if (!painel) return;
    painel.classList.remove('hidden');

    const notas = dados?.notas || [];
    const lacunas = detectarLacunas(notas);
    const qtdLacunas = lacunas.reduce((s, l) => s + l.quantidade, 0);
    const falhas = Number(dados?.total_erros || (dados?.erros || []).length || 0);
    const duplicidades = Number((dados?.duplicidades || []).length || 0);
    const naoClassificadas = notas.filter(n => n.operacao === 'Não classificada').length;
    const alertasTrib = (dados?.auditoria || []).filter(a => !['OK', 'Válido'].includes(String(a.status || ''))).length;

    const set = (id, valor) => { const el = document.getElementById(id); if (el) el.textContent = Number(valor).toLocaleString('pt-BR'); };
    set('diag-falhas', falhas);
    set('diag-lacunas', qtdLacunas);
    set('diag-duplicidades', duplicidades);
    set('diag-nao-class', naoClassificadas);
    set('diag-tributarios', alertasTrib);

    const criticos = falhas + duplicidades + naoClassificadas;
    const atencoes = qtdLacunas + alertasTrib;
    const status = document.getElementById('omnixml-diagnostico-status');
    if (status) {
      if (criticos > 0) { status.textContent = 'REVISÃO NECESSÁRIA'; status.className = 'px-4 py-2 rounded-xl text-sm font-bold bg-rose-100 text-rose-700'; }
      else if (atencoes > 0) { status.textContent = 'CONFERIR ALERTAS'; status.className = 'px-4 py-2 rounded-xl text-sm font-bold bg-amber-100 text-amber-700'; }
      else { status.textContent = 'SEM PENDÊNCIAS DETECTADAS'; status.className = 'px-4 py-2 rounded-xl text-sm font-bold bg-emerald-100 text-emerald-700'; }
    }

    const lista = [];
    if (falhas) lista.push(item('critico', `${falhas} XML(s) com falha fiscal`, 'Há documentos que não passaram nas validações de integridade/autorização.', 'tab-erros'));
    if (qtdLacunas) lista.push(item('atencao', `${qtdLacunas} número(s) ausente(s) na sequência`, 'Confirme se são inutilizações, documentos não exportados ou arquivos ausentes.'));
    if (duplicidades) lista.push(item('critico', `${duplicidades} duplicidade(s) de chave`, 'A mesma chave fiscal apareceu mais de uma vez na consulta.'));
    if (naoClassificadas) lista.push(item('critico', `${naoClassificadas} documento(s) sem classificação Entrada/Saída`, 'O CNPJ da empresa não correspondeu ao emitente nem ao destinatário.', 'tab-nfe'));
    if (alertasTrib) lista.push(item('atencao', `${alertasTrib} combinação(ões) tributária(s) para revisar`, 'Há alertas nas regras de NCM, CFOP e CST/CSOSN.', 'tab-auditoria'));
    if (!lista.length) lista.push(item('ok', 'Nenhuma pendência detectada pelas regras atuais', 'A base carregada passou nas verificações implementadas pelo OmniXML.'));
    document.getElementById('omnixml-diagnostico-lista').innerHTML = lista.join('');

    const detalhes = document.getElementById('omnixml-lacunas-detalhes');
    const body = document.getElementById('omnixml-lacunas-body');
    if (detalhes && body) {
      if (lacunas.length) {
        detalhes.classList.remove('hidden');
        body.innerHTML = lacunas.map(l => `<tr class="border-t border-slate-100"><td class="p-3 font-semibold">${esc(l.modelo)}</td><td class="p-3 font-mono">${esc(l.serie)}</td><td class="p-3 font-mono">${l.de === l.ate ? l.de : `${l.de} a ${l.ate}`}</td><td class="p-3 font-bold text-amber-700">${l.quantidade.toLocaleString('pt-BR')}</td><td class="p-3 font-mono text-xs text-slate-500">${l.amostra.join(', ')}${l.truncada ? ', …' : ''}</td></tr>`).join('');
      } else {
        detalhes.classList.add('hidden');
        body.innerHTML = '';
      }
    }

    painel.querySelectorAll('[data-diag-aba]').forEach(btn => btn.onclick = () => abrirAba(btn.dataset.diagAba));
  }

  window.atualizarPainelDinamico = function(dados) {
    const retorno = original.apply(this, arguments);
    try { renderizar(dados || {}); } catch (err) { console.error('OmniXML diagnóstico:', err); }
    return retorno;
  };

  document.addEventListener('DOMContentLoaded', garantirPainel);
})();
