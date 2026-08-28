(() => {
  const original = window.atualizarPainelDinamico;
  if (typeof original !== 'function') return;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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

  // Regra fiscal do diagnóstico de sequência:
  // 1) considera SOMENTE documentos classificados como Saída da empresa auditada;
  // 2) separa por modelo + série;
  // 3) usa apenas o menor e o maior número realmente encontrados na pasta carregada;
  // 4) aponta os números ausentes somente dentro desse intervalo.
  // NF-e de Entrada/fornecedores nunca participa desta conferência.
  function detectarLacunas(notas) {
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

    const lacunas = [];
    for (const grupo of grupos.values()) {
      const nums = Array.from(grupo.numeros).sort((a, b) => a - b);
      if (nums.length < 2) continue;
      const inicial = nums[0];
      const final = nums[nums.length - 1];
      const existentes = grupo.numeros;
      const ausentes = [];
      let quantidade = 0;
      for (let n = inicial; n <= final; n++) {
        if (!existentes.has(n)) {
          quantidade++;
          if (ausentes.length < 100) ausentes.push(n);
        }
      }
      if (!quantidade) continue;
      lacunas.push({
        modelo: grupo.modelo,
        serie: grupo.serie,
        inicial,
        final,
        quantidade,
        ausentes,
        truncada: quantidade > ausentes.length
      });
    }
    return lacunas;
  }

  function garantirPainel() {
    if (document.getElementById('omnixml-diagnostico-v2')) return;
    const tab = document.getElementById('tab-resumo');
    const resumo = document.getElementById('faixa-resumo-auditoria');
    if (!tab) return;

    const sec = document.createElement('section');
    sec.id = 'omnixml-diagnostico-v2';
    sec.className = 'hidden mb-5';
    sec.innerHTML = `
      <button id="omnixml-diag-toggle" type="button" class="w-full rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm flex items-center justify-between gap-4 hover:bg-slate-50 transition-colors text-left">
        <div class="flex items-center gap-3 min-w-0">
          <span class="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">✓</span>
          <div class="min-w-0">
            <div class="font-bold text-slate-800">Diagnóstico do fechamento</div>
            <div id="omnixml-diag-resumo" class="text-sm text-slate-500 truncate">Verificações adicionais disponíveis</div>
          </div>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <span id="omnixml-diag-status" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 text-slate-600">VER DETALHES</span>
          <span id="omnixml-diag-seta" class="text-slate-400">⌄</span>
        </div>
      </button>
      <div id="omnixml-diag-conteudo" class="hidden mt-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div class="rounded-lg bg-rose-50 p-3"><div class="text-[11px] uppercase font-bold text-rose-500">Falhas fiscais</div><div id="diag-falhas-v2" class="text-xl font-black text-rose-700">0</div></div>
          <div class="rounded-lg bg-amber-50 p-3"><div class="text-[11px] uppercase font-bold text-amber-600">Lacunas nas saídas</div><div id="diag-lacunas-v2" class="text-xl font-black text-amber-700">0</div></div>
          <div class="rounded-lg bg-orange-50 p-3"><div class="text-[11px] uppercase font-bold text-orange-600">Duplicidades</div><div id="diag-dup-v2" class="text-xl font-black text-orange-700">0</div></div>
          <div class="rounded-lg bg-violet-50 p-3"><div class="text-[11px] uppercase font-bold text-violet-600">Alertas tributários</div><div id="diag-trib-v2" class="text-xl font-black text-violet-700">0</div></div>
        </div>
        <div id="omnixml-diag-explicacao" class="text-sm text-slate-600 mb-4"></div>
        <div id="omnixml-lacunas-v2" class="hidden overflow-x-auto rounded-lg border border-slate-200">
          <table class="w-full text-sm text-left"><thead class="bg-slate-50 text-xs uppercase text-slate-500"><tr><th class="p-3">Modelo</th><th class="p-3">Série</th><th class="p-3">Inicial na pasta</th><th class="p-3">Final na pasta</th><th class="p-3">Números ausentes</th></tr></thead><tbody id="omnixml-lacunas-v2-body"></tbody></table>
        </div>
        <p class="mt-4 text-xs text-slate-400">Lacuna = número ausente entre o primeiro e o último documento de SAÍDA encontrados na pasta carregada, dentro do mesmo modelo e série. Documentos de entrada não participam desta conferência.</p>
      </div>`;

    if (resumo && resumo.parentElement === tab) resumo.insertAdjacentElement('afterend', sec); else tab.prepend(sec);
    const btn = sec.querySelector('#omnixml-diag-toggle');
    btn.onclick = () => {
      const conteudo = sec.querySelector('#omnixml-diag-conteudo');
      const seta = sec.querySelector('#omnixml-diag-seta');
      const abrir = conteudo.classList.contains('hidden');
      conteudo.classList.toggle('hidden', !abrir);
      seta.textContent = abrir ? '⌃' : '⌄';
    };
  }

  function renderizar(dados) {
    garantirPainel();
    const sec = document.getElementById('omnixml-diagnostico-v2');
    if (!sec) return;
    sec.classList.remove('hidden');

    const notas = dados?.notas || [];
    const lacunas = detectarLacunas(notas);
    const qtdLacunas = lacunas.reduce((s, l) => s + l.quantidade, 0);
    const falhas = Number(dados?.total_erros || (dados?.erros || []).length || 0);
    const duplicidades = Number((dados?.duplicidades || []).length || 0);
    const alertasTrib = (dados?.auditoria || []).filter(a => !['OK', 'Válido'].includes(String(a.status || ''))).length;

    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = Number(v).toLocaleString('pt-BR'); };
    set('diag-falhas-v2', falhas); set('diag-lacunas-v2', qtdLacunas); set('diag-dup-v2', duplicidades); set('diag-trib-v2', alertasTrib);

    const partes = [];
    if (falhas) partes.push(`${falhas} falha${falhas === 1 ? '' : 's'} fiscal${falhas === 1 ? '' : 'is'}`);
    if (qtdLacunas) partes.push(`${qtdLacunas} número${qtdLacunas === 1 ? '' : 's'} ausente${qtdLacunas === 1 ? '' : 's'} nas saídas`);
    if (duplicidades) partes.push(`${duplicidades} duplicidade${duplicidades === 1 ? '' : 's'}`);
    if (alertasTrib) partes.push(`${alertasTrib} alerta${alertasTrib === 1 ? '' : 's'} tributário${alertasTrib === 1 ? '' : 's'}`);
    const resumo = document.getElementById('omnixml-diag-resumo');
    if (resumo) resumo.textContent = partes.length ? partes.join(' • ') : 'Nenhuma pendência adicional detectada';

    const status = document.getElementById('omnixml-diag-status');
    if (status) {
      if (falhas || duplicidades) { status.textContent = 'REVISAR'; status.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-100 text-rose-700'; }
      else if (qtdLacunas || alertasTrib) { status.textContent = 'CONFERIR'; status.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-100 text-amber-700'; }
      else { status.textContent = 'OK'; status.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-700'; }
    }

    const exp = document.getElementById('omnixml-diag-explicacao');
    if (exp) exp.innerHTML = `<strong>O que isto faz?</strong> A conferência de sequência usa somente documentos de <strong>Saída</strong> emitidos pela empresa auditada. Para cada modelo e série existentes na pasta atual, considera o primeiro e o último número encontrados e procura números ausentes entre eles. NF-e de entrada de fornecedores fica fora desta análise.`;

    const box = document.getElementById('omnixml-lacunas-v2');
    const body = document.getElementById('omnixml-lacunas-v2-body');
    if (box && body) {
      if (lacunas.length) {
        box.classList.remove('hidden');
        body.innerHTML = lacunas.map(l => `<tr class="border-t border-slate-100"><td class="p-3 font-semibold">${esc(l.modelo)}</td><td class="p-3 font-mono">${esc(l.serie)}</td><td class="p-3 font-mono">${l.inicial}</td><td class="p-3 font-mono">${l.final}</td><td class="p-3 font-mono text-amber-700">${l.ausentes.join(', ')}${l.truncada ? ', …' : ''} <span class="text-slate-400">(${l.quantidade.toLocaleString('pt-BR')} ausente${l.quantidade === 1 ? '' : 's'})</span></td></tr>`).join('');
      } else { box.classList.add('hidden'); body.innerHTML = ''; }
    }
  }

  window.atualizarPainelDinamico = function(dados) {
    const retorno = original.apply(this, arguments);
    try { renderizar(dados || {}); } catch (err) { console.error('OmniXML diagnóstico v2:', err); }
    return retorno;
  };

  document.addEventListener('DOMContentLoaded', garantirPainel);
})();