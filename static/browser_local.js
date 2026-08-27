(() => {
  let ultimoDashboard = null;

  const modalHtml = `
  <div id="omnixml-local-modal" class="fixed inset-0 z-[9999] hidden items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
    <div class="w-full max-w-2xl rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden">
      <div class="px-6 py-5 border-b border-slate-200 flex items-start justify-between gap-4">
        <div>
          <h2 class="text-xl font-black text-slate-800">Importar documentos fiscais</h2>
          <p class="text-sm text-slate-500 mt-1">Os XMLs são processados no seu navegador. Eles não são enviados ao servidor.</p>
        </div>
        <button id="omnixml-local-fechar" class="text-slate-400 hover:text-slate-700 text-xl">×</button>
      </div>
      <div class="p-6 grid md:grid-cols-3 gap-4">
        <button id="omnixml-local-arquivos" class="rounded-xl border border-blue-200 bg-blue-50 hover:bg-blue-100 p-5 text-left">
          <div class="font-bold text-blue-700">Selecionar XMLs</div>
          <div class="text-xs text-slate-500 mt-1">Selecione vários XMLs de uma vez.</div>
        </button>
        <button id="omnixml-local-pasta" class="rounded-xl border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 p-5 text-left">
          <div class="font-bold text-emerald-700">Pasta inteira</div>
          <div class="text-xs text-slate-500 mt-1">Inclui XMLs existentes nas subpastas.</div>
        </button>
        <button id="omnixml-local-cancelar" class="rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 p-5 text-left">
          <div class="font-bold text-slate-700">Cancelar</div>
          <div class="text-xs text-slate-500 mt-1">Voltar ao dashboard.</div>
        </button>
      </div>
      <div class="px-6 pb-6 text-xs text-slate-500">
        Privacidade: nenhum XML sai deste computador. Para ZIP, extraia o arquivo e selecione a pasta.
      </div>
    </div>
  </div>
  <input id="omnixml-local-input-arquivos" class="hidden" type="file" multiple accept=".xml,text/xml,application/xml">
  <input id="omnixml-local-input-pasta" class="hidden" type="file" multiple webkitdirectory directory accept=".xml,text/xml,application/xml">
  `;

  const txt = (el, def = '') => el && el.textContent != null ? el.textContent.trim() : def;
  const child = (el, name) => {
    if (!el) return null;
    for (const node of el.children || []) if ((node.localName || node.nodeName) === name) return node;
    return null;
  };
  const desc = (el, name) => {
    if (!el) return null;
    const list = el.getElementsByTagNameNS ? el.getElementsByTagNameNS('*', name) : [];
    if (list && list.length) return list[0];
    for (const node of el.getElementsByTagName('*')) if ((node.localName || node.nodeName) === name) return node;
    return null;
  };
  const all = (el, name) => {
    if (!el) return [];
    const list = el.getElementsByTagNameNS ? el.getElementsByTagNameNS('*', name) : [];
    if (list && list.length) return Array.from(list);
    return Array.from(el.getElementsByTagName('*')).filter(n => (n.localName || n.nodeName) === name);
  };
  const num = value => {
    const n = Number(String(value ?? '').replace(',', '.'));
    return Number.isFinite(n) ? n : 0;
  };

  function status(texto, cor = 'blue') {
    const el = document.getElementById('statusAuditoria');
    if (!el) return;
    const cls = cor === 'emerald' ? 'bg-emerald-500' : cor === 'red' ? 'bg-red-500' : 'bg-blue-500 animate-pulse';
    el.innerHTML = `<span class="w-2 h-2 rounded-full ${cls}"></span> ${escapeHtml(texto)}`;
  }

  function progresso(atual, total) {
    const container = document.getElementById('progressContainer');
    const bar = document.getElementById('progressBar');
    if (!container || !bar) return;
    container.style.display = 'block';
    bar.style.width = `${total ? Math.min(100, atual / total * 100) : 0}%`;
  }

  function parseEvento(root, arquivo) {
    const infs = all(root, 'infEvento');
    const pedido = infs.find(i => txt(child(i, 'tpEvento')) === '110111');
    if (!pedido) return null;
    const chave = txt(child(pedido, 'chNFe'));
    if (!chave) return null;
    let cstat = '', motivo = '';
    for (const inf of infs) {
      const c = txt(child(inf, 'cStat'));
      if (c) { cstat = c; motivo = txt(child(inf, 'xMotivo')); }
    }
    return {tipo: 'cancelamento', arquivo, chave, confirmado: ['135','155'].includes(cstat), cstat, motivo};
  }

  function parseNFe(root, arquivo) {
    const inf = desc(root, 'infNFe');
    if (!inf) return null;
    const ide = child(inf, 'ide');
    const emit = child(inf, 'emit');
    const total = desc(inf, 'ICMSTot');
    const modelo = txt(child(ide, 'mod'));
    const id = inf.getAttribute('Id') || '';
    const chave = id.startsWith('NFe') ? id.slice(3) : id;
    const itens = [];

    for (const det of all(inf, 'det')) {
      const prod = child(det, 'prod');
      if (!prod) continue;
      let cst = 'N/A';
      const icms = desc(det, 'ICMS');
      if (icms) {
        for (const grupo of icms.children || []) {
          const c = txt(child(grupo, 'CST')) || txt(child(grupo, 'CSOSN'));
          if (c) { cst = c; break; }
        }
      }
      const bruto = num(txt(child(prod, 'vProd')));
      const desconto = num(txt(child(prod, 'vDesc')));
      itens.push({
        codigo: txt(child(prod, 'cProd'), 'N/A'), cprod: txt(child(prod, 'cProd'), 'N/A'),
        nome: txt(child(prod, 'xProd'), 'N/A'), ncm: txt(child(prod, 'NCM'), 'N/A'),
        unidade: txt(child(prod, 'uCom'), 'N/A'), cfop: txt(child(prod, 'CFOP'), 'N/A'),
        cst, qtd: num(txt(child(prod, 'qCom'))), valor_bruto: bruto, desconto, valor: bruto - desconto
      });
    }

    const tpNF = txt(child(ide, 'tpNF'));
    const emissao = txt(child(ide, 'dhEmi')) || txt(child(ide, 'dEmi'));
    return {
      arquivo,
      chave,
      numero_nota: txt(child(ide, 'nNF'), 'N/A'),
      numero: txt(child(ide, 'nNF'), 'N/A'),
      serie: txt(child(ide, 'serie'), 'N/A'),
      data: emissao ? emissao.slice(0,10) : 'N/A',
      valor: num(txt(child(total, 'vNF'))),
      tipo: modelo === '65' ? 'NFC-e (Mod. 65)' : 'NF-e (Mod. 55)',
      operacao: tpNF === '0' ? 'Entrada' : 'Saída',
      status: 'OK',
      emitente_nome: txt(child(emit, 'xNome'), 'Desconhecido'),
      emitente: txt(child(emit, 'xNome'), 'Desconhecido'),
      itens
    };
  }

  async function lerArquivo(file) {
    const xml = await file.text();
    const doc = new DOMParser().parseFromString(xml, 'application/xml');
    const erro = doc.querySelector('parsererror');
    if (erro) throw new Error('XML malformado ou inválido.');
    const root = doc.documentElement;
    const nome = root.localName || root.nodeName;
    if (['evento','procEventoNFe','retEvento'].includes(nome)) return parseEvento(root, file.webkitRelativePath || file.name);
    if (['NFe','nfeProc'].includes(nome)) return parseNFe(root, file.webkitRelativePath || file.name);
    return {tipo: 'ignorado', arquivo: file.webkitRelativePath || file.name, motivo: `Documento ${nome} ainda não tratado no dashboard fiscal.`};
  }

  function montarDashboard(resultados, erros, totalLidos) {
    const canceladas = new Set(resultados.filter(r => r?.tipo === 'cancelamento' && r.confirmado).map(r => r.chave));
    const notas = [];
    const vistas = new Map();
    const duplicidades = [];
    for (const r of resultados) {
      if (!r || r.tipo === 'cancelamento' || r.tipo === 'ignorado') continue;
      if (r.chave && vistas.has(r.chave)) {
        duplicidades.push({chave:r.chave, arquivo_original:vistas.get(r.chave).arquivo, arquivo_duplicado:r.arquivo});
        continue;
      }
      if (r.chave) vistas.set(r.chave, r);
      if (canceladas.has(r.chave)) r.status = 'Cancelado';
      notas.push(r);
    }

    const cfop = new Map(), cst = new Map(), serie = new Map(), diario = new Map(), audit = new Map(), produtos = new Map();
    const cfopsSt = new Set(['5405','5403','5401','6404','6403','6401']);
    const cstsSt = new Set(['60','060','500','201','202','203']);

    for (const n of notas) {
      if (String(n.status).includes('Cancelado') || n.valor <= 0) continue;
      if (n.operacao === 'Saída') {
        const chaveSerie = `${n.tipo}_${n.serie}`;
        const s = serie.get(chaveSerie) || {tipo:n.tipo, serie:n.serie, valor:0}; s.valor += n.valor; serie.set(chaveSerie,s);
        const faturar = !(n.itens || []).some(i => ['5929','6929'].includes(i.cfop));
        if (faturar) diario.set(n.data, (diario.get(n.data)||0) + n.valor);
      }
      for (const i of n.itens || []) {
        if (n.operacao === 'Saída') {
          const kc = `${n.tipo}_${i.cfop}`; const c = cfop.get(kc)||{tipo:n.tipo,cfop:i.cfop,valor:0}; c.valor += i.valor; cfop.set(kc,c);
          const ks = `${n.tipo}_${i.cst}`; const s = cst.get(ks)||{tipo:n.tipo,cst:i.cst,valor:0}; s.valor += i.valor; cst.set(ks,s);
          const ka = `${i.ncm}_${i.cfop}_${i.cst}`;
          if (!audit.has(ka)) {
            let st='OK';
            if (!/^\d{8}$/.test(i.ncm)) st='NCM INVÁLIDO';
            else if (cfopsSt.has(i.cfop) && !cstsSt.has(i.cst)) st='ALERTA: CFOP de ST com CST/CSOSN atípico';
            else if (!cfopsSt.has(i.cfop) && cstsSt.has(i.cst)) st='ALERTA: CST/CSOSN de ST com CFOP a revisar';
            audit.set(ka,{ncm:i.ncm,cfop:i.cfop,cst:i.cst,status:st,valor:0,operacao:n.operacao});
          }
          audit.get(ka).valor += i.valor;
        }
        if (n.tipo.includes('NFC-e')) {
          const kp = `${i.codigo}_${i.cfop}_${i.cst}`;
          if (!produtos.has(kp)) {
            let st='OK', motivo='Sem divergências nas regras atualmente verificadas.';
            if (!/^\d{8}$/.test(i.ncm)) {st='Erro: NCM inválido'; motivo='O NCM deve possuir 8 dígitos numéricos.';}
            produtos.set(kp,{codigo:i.codigo,ncm:i.ncm,produto:String(i.nome||'').replace(/^B\d{2}[-\s]*/,'').slice(0,50),cfop:i.cfop,cst:i.cst,status:st,motivo});
          }
        }
      }
    }

    return {
      status:'sucesso',
      notas:notas.map(n => {const x={...n}; delete x.itens; return x;}),
      cfop:Array.from(cfop.values()).filter(x=>x.valor>0), cst:Array.from(cst.values()).filter(x=>x.valor>0),
      serie:Array.from(serie.values()).filter(x=>x.valor>0), auditoria:Array.from(audit.values()), produtos:Array.from(produtos.values()),
      diario:Array.from(diario.entries()).sort(([a],[b])=>a.localeCompare(b)).map(([data,valor])=>({data,valor})),
      erros, total_erros:erros.length, total_lidos:totalLidos, duplicidades, avisos:[]
    };
  }

  async function processarLocal(fileList, fechar) {
    const files = Array.from(fileList || []).filter(f => /\.xml$/i.test(f.name));
    if (!files.length) { alert('Nenhum XML foi selecionado. Para ZIP, extraia o arquivo e selecione a pasta.'); return; }
    fechar();
    const btn = document.getElementById('btnProcessarDash');
    if (btn) { btn.disabled=true; btn.innerHTML='Processando...'; }
    const resultados=[], erros=[];
    try {
      for (let i=0;i<files.length;i++) {
        const file=files[i];
        status(`Processando localmente: ${i+1} de ${files.length} XMLs`);
        progresso(i+1, files.length);
        try {
          const r=await lerArquivo(file);
          if (r?.tipo==='ignorado') erros.push({arquivo:r.arquivo,motivo:r.motivo,caminho:r.arquivo});
          else if (r) resultados.push(r);
        } catch (e) {
          erros.push({arquivo:file.webkitRelativePath||file.name,motivo:e.message||'Falha ao ler XML.',caminho:file.webkitRelativePath||file.name});
        }
        if (i % 25 === 24) await new Promise(resolve => setTimeout(resolve, 0));
      }
      const dados=montarDashboard(resultados,erros,files.length);
      ultimoDashboard=dados;
      aplicarDashboard(dados);
    } catch (e) {
      console.error(e); status(e.message||'Falha no processamento local.','red'); alert(e.message||'Falha no processamento local.');
    } finally {
      if (btn) { btn.disabled=false; btn.innerHTML='Importar e Auditar XMLs'; }
      setTimeout(()=>{const c=document.getElementById('progressContainer');if(c)c.style.display='none';},2500);
    }
  }

  function aplicarDashboard(dados) {
    xmlNotasGlobais = dados.notas || [];
    dtCancelados.clear().rows.add((dados.notas||[]).filter(n=>String(n.status||'').includes('Cancelado'))).draw();
    dtNFCe.clear().rows.add((dados.notas||[]).filter(n=>String(n.tipo||'').includes('NFC-e'))).draw();
    dtNFe.clear().rows.add((dados.notas||[]).filter(n=>String(n.tipo||'').includes('NF-e'))).draw();
    dtCFOP.clear().rows.add(dados.cfop||[]).draw(); dtCST.clear().rows.add(dados.cst||[]).draw();
    dtSerie.clear().rows.add(dados.serie||[]).draw(); dtAuditoria.clear().rows.add(dados.auditoria||[]).draw();
    dtProdutos.clear().rows.add(dados.produtos||[]).draw(); dtErros.clear().rows.add(dados.erros||[]).draw();
    atualizarPainelDinamico(dados); renderizarGraficos(dados.cfop||[],dados.cst||[],dados.diario||[]);
    const empresa=(dados.notas||[]).find(n=>n.operacao==='Saída'&&(n.emitente_nome||n.emitente)) || (dados.notas||[]).find(n=>n.emitente_nome||n.emitente);
    const header=document.getElementById('nomeEmpresaHeader'); if(header) header.innerText=empresa?(empresa.emitente_nome||empresa.emitente):'Empresa não identificada';
    status(`Auditoria concluída localmente (${dados.total_lidos||0} arquivos lidos)`,'emerald');
    document.getElementById('faixa-resumo-auditoria')?.classList.remove('hidden');
    document.getElementById('btnTrocarCliente')?.classList.remove('hidden');
    document.getElementById('btnExportarGeral')?.classList.remove('hidden');
    document.getElementById('card-boas-vindas')?.classList.add('hidden');
  }

  function exportarCsv() {
    if (!ultimoDashboard) return;
    const rows=[['Arquivo','Tipo','Numero','Serie','Data','Operacao','Valor','Status','Chave']];
    for(const n of ultimoDashboard.notas||[]) rows.push([n.arquivo,n.tipo,n.numero||n.numero_nota,n.serie,n.data,n.operacao,n.valor,n.status,n.chave]);
    for(const e of ultimoDashboard.erros||[]) rows.push([e.arquivo,'','','','','','',e.motivo,'']);
    const csv='\ufeff'+rows.map(r=>r.map(v=>`"${String(v??'').replaceAll('"','""')}"`).join(';')).join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download='omnixml-relatorio.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  function escapeHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

  function instalar() {
    document.body.insertAdjacentHTML('beforeend',modalHtml);
    const modal=document.getElementById('omnixml-local-modal');
    const abrir=()=>{modal.classList.remove('hidden');modal.classList.add('flex');};
    const fechar=()=>{modal.classList.add('hidden');modal.classList.remove('flex');};
    document.getElementById('omnixml-local-fechar').onclick=fechar; document.getElementById('omnixml-local-cancelar').onclick=fechar;
    document.getElementById('omnixml-local-arquivos').onclick=()=>document.getElementById('omnixml-local-input-arquivos').click();
    document.getElementById('omnixml-local-pasta').onclick=()=>document.getElementById('omnixml-local-input-pasta').click();
    document.getElementById('omnixml-local-input-arquivos').addEventListener('change',e=>processarLocal(e.target.files,fechar));
    document.getElementById('omnixml-local-input-pasta').addEventListener('change',e=>processarLocal(e.target.files,fechar));
    window.iniciarProcessamento=abrir;
    window.limparESairCliente=()=>{if(confirm('Deseja limpar a consulta atual e iniciar uma nova?')) location.reload();};
    window.exportarRelatorioGeral=exportarCsv;
    window.confrontarSPED=()=>alert('O SPED será adaptado para processamento local na próxima etapa.');
    window.importarPisCofins=()=>alert('A EFD-Contribuições será adaptada para processamento local na próxima etapa.');
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',instalar); else instalar();
})();
