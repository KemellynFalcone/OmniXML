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
  const codigoModelo = modelo => modelo === 'NFC-e' ? '65' : modelo === 'NF-e' ? '55' : '';

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

      const faixas = (inutilizacoes || []).filter(i => i?.homologada && String(i.modelo) === codigoModelo(grupo.modelo) && String(i.serie) === grupo.serie);
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
        <div class="flex items-center gap-3 min-w-0"><span class="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">✓</span><div class="min-w-0"><div class="font-bold text-slate-800">Diagnóstico do fechamento</div><div id="omnixml-diag-resumo" class="text-sm text-slate-500 truncate">Verificações adicionais disponíveis</div></div></div>
        <div class="flex items-center gap-3 shrink-0"><span id="omnixml-diag-status" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 text-slate-600">VER DETALHES</span><span id="omnixml-diag-seta" class="text-slate-400">⌄</span></div>
      </button>
      <div id="omnixml-diag-conteudo" class="hidden mt-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          <div class="rounded-lg bg-rose-50 p-3"><div class="text-[11px] uppercase font-bold text-rose-500">Falhas fiscais</div><div id="diag-falhas-v2" class="text-xl font-black text-rose-700">0</div></div>
          <div class="rounded-lg bg-amber-50 p-3"><div class="text-[11px] uppercase font-bold text-amber-600">A conferir</div><div id="diag-lacunas-v2" class="text-xl font-black text-amber-700">0</div></div>
          <div class="rounded-lg bg-blue-50 p-3"><div class="text-[11px] uppercase font-bold text-blue-600">Inutilizadas</div><div id="diag-inutil-v2" class="text-xl font-black text-blue-700">0</div></div>
          <div class="rounded-lg bg-orange-50 p-3"><div class="text-[11px] uppercase font-bold text-orange-600">Duplicidades</div><div id="diag-dup-v2" class="text-xl font-black text-orange-700">0</div></div>
          <div class="rounded-lg bg-violet-50 p-3"><div class="text-[11px] uppercase font-bold text-violet-600">Alertas tributários</div><div id="diag-trib-v2" class="text-xl font-black text-violet-700">0</div></div>
        </div>
        <div id="omnixml-diag-explicacao" class="text-sm text-slate-600 mb-4"></div>
        <div id="omnixml-lacunas-v2" class="hidden overflow-x-auto rounded-lg border border-slate-200">
          <table class="w-full text-sm text-left"><thead class="bg-slate-50 text-xs uppercase text-slate-500"><tr><th class="p-3">Modelo</th><th class="p-3">Série</th><th class="p-3">Inicial</th><th class="p-3">Final</th><th class="p-3">Inutilizadas</th><th class="p-3">A conferir</th></tr></thead><tbody id="omnixml-lacunas-v2-body"></tbody></table>
        </div>
        <p class="mt-4 text-xs text-slate-400">Canceladas continuam ocupando a numeração porque o XML da nota existe. Inutilizações homologadas (cStat 102) justificam números sem NF-e/NFC-e. Só números sem nota e sem inutilização homologada ficam em “A conferir”.</p>
      </div>`;
    if (resumo && resumo.parentElement === tab) resumo.insertAdjacentElement('afterend', sec); else tab.prepend(sec);
    sec.querySelector('#omnixml-diag-toggle').onclick = () => { const c=sec.querySelector('#omnixml-diag-conteudo'), s=sec.querySelector('#omnixml-diag-seta'), abrir=c.classList.contains('hidden'); c.classList.toggle('hidden', !abrir); s.textContent=abrir?'⌃':'⌄'; };
  }

  function renderizar(dados) {
    garantirPainel();
    const sec = document.getElementById('omnixml-diagnostico-v2');
    if (!sec) return;
    sec.classList.remove('hidden');
    const notas = dados?.notas || [];
    const inutilizacoes = window.__omnixmlInutilizacoes || [];
    const grupos = detectarLacunas(notas, inutilizacoes);
    const qtdConferir = grupos.reduce((s,g)=>s+g.conferir.length,0);
    const qtdInutilizadas = grupos.reduce((s,g)=>s+g.inutilizadas.length,0);
    const falhas = Number(dados?.total_erros || (dados?.erros || []).length || 0);
    const duplicidades = Number((dados?.duplicidades || []).length || 0);
    const alertasTrib = (dados?.auditoria || []).filter(a => !['OK','Válido'].includes(String(a.status || ''))).length;
    const set=(id,v)=>{const el=document.getElementById(id);if(el)el.textContent=Number(v).toLocaleString('pt-BR');};
    set('diag-falhas-v2',falhas); set('diag-lacunas-v2',qtdConferir); set('diag-inutil-v2',qtdInutilizadas); set('diag-dup-v2',duplicidades); set('diag-trib-v2',alertasTrib);

    const partes=[];
    if(falhas)partes.push(`${falhas} falha${falhas===1?'':'s'} fiscal${falhas===1?'':'is'}`);
    if(qtdInutilizadas)partes.push(`${qtdInutilizadas} inutilizaç${qtdInutilizadas===1?'ão':'ões'} justificada${qtdInutilizadas===1?'':'s'}`);
    if(qtdConferir)partes.push(`${qtdConferir} número${qtdConferir===1?'':'s'} a conferir`);
    if(duplicidades)partes.push(`${duplicidades} duplicidade${duplicidades===1?'':'s'}`);
    if(alertasTrib)partes.push(`${alertasTrib} alerta${alertasTrib===1?'':'s'} tributário${alertasTrib===1?'':'s'}`);
    document.getElementById('omnixml-diag-resumo').textContent=partes.length?partes.join(' • '):'Nenhuma pendência adicional detectada';
    const status=document.getElementById('omnixml-diag-status');
    if(status){ if(falhas||duplicidades){status.textContent='REVISAR';status.className='px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-100 text-rose-700';} else if(qtdConferir||alertasTrib){status.textContent='CONFERIR';status.className='px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-100 text-amber-700';} else {status.textContent='OK';status.className='px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-700';} }
    const exp=document.getElementById('omnixml-diag-explicacao');
    if(exp)exp.innerHTML='<strong>O que isto faz?</strong> Confere somente a sequência de <strong>Saídas</strong> da empresa. Números ocupados por notas canceladas continuam existentes. Quando falta uma nota, o OmniXML procura uma inutilização homologada na pasta e só mantém como pendência o número sem justificativa.';
    const box=document.getElementById('omnixml-lacunas-v2'), body=document.getElementById('omnixml-lacunas-v2-body');
    if(box&&body){ if(grupos.length){box.classList.remove('hidden');body.innerHTML=grupos.map(g=>`<tr class="border-t border-slate-100"><td class="p-3 font-semibold">${esc(g.modelo)}</td><td class="p-3 font-mono">${esc(g.serie)}</td><td class="p-3 font-mono">${g.inicial}</td><td class="p-3 font-mono">${g.final}</td><td class="p-3 font-mono text-blue-700">${g.inutilizadas.length?g.inutilizadas.map(x=>x.numero).join(', '):'—'}</td><td class="p-3 font-mono ${g.conferir.length?'text-amber-700':'text-emerald-700'}">${g.conferir.length?g.conferir.join(', '):'Nenhum ✓'}</td></tr>`).join('');}else{box.classList.add('hidden');body.innerHTML='';} }
  }

  window.atualizarPainelDinamico=function(dados){const retorno=original.apply(this,arguments);try{renderizar(dados||{});}catch(err){console.error('OmniXML diagnóstico v2:',err);}return retorno;};
  document.addEventListener('DOMContentLoaded',garantirPainel);
})();
