(() => {
  const originalText = File.prototype.text;
  const metadados = new Map();

  const nomeArquivo = file => file.webkitRelativePath || file.name || 'arquivo.xml';
  const localName = node => node ? (node.localName || node.nodeName || '') : '';
  const first = (root, name) => {
    if (!root) return null;
    const ns = root.getElementsByTagNameNS ? root.getElementsByTagNameNS('*', name) : [];
    if (ns && ns.length) return ns[0];
    for (const node of root.getElementsByTagName('*')) if (localName(node) === name) return node;
    return null;
  };
  const txt = node => node && node.textContent ? node.textContent.trim() : '';
  const moeda = valor => Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const escape = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

  function extrair(xml, arquivo) {
    try {
      const doc = new DOMParser().parseFromString(xml, 'application/xml');
      if (doc.querySelector('parsererror')) return;
      const inf = first(doc, 'infNFe');
      if (!inf) return;
      const ide = first(inf, 'ide');
      const total = first(inf, 'ICMSTot');
      const id = (inf.getAttribute('Id') || '').replace(/^NFe/, '');
      const modelo = txt(first(ide, 'mod'));
      metadados.set(arquivo, {
        arquivo,
        chave: id,
        numero: txt(first(ide, 'nNF')),
        serie: txt(first(ide, 'serie')),
        modelo,
        tipo: modelo === '65' ? 'NFC-e' : modelo === '55' ? 'NF-e' : `Mod. ${modelo || '?'}`,
        valor: Number(txt(first(total, 'vNF')).replace(',', '.')) || 0
      });
    } catch (_) {}
  }

  File.prototype.text = async function(...args) {
    const xml = await originalText.apply(this, args);
    extrair(xml, nomeArquivo(this));
    return xml;
  };

  function motivoCurto(motivo) {
    const m = String(motivo || 'Falha de validação fiscal.');
    if (/sem protocolo|nfeProc|protNFe/i.test(m)) return 'Sem protocolo SEFAZ';
    if (/contingência/i.test(m)) return 'Contingência sem protocolo';
    if (/assinatura/i.test(m)) return 'Sem assinatura digital';
    if (/cStat/i.test(m)) return 'Status SEFAZ inválido';
    if (/QR Code/i.test(m)) return 'NFC-e sem QR Code';
    if (/malformado|inválido/i.test(m)) return 'XML inválido';
    return m.length > 52 ? `${m.slice(0, 49)}...` : m;
  }

  function garantirPainel() {
    const tab = document.getElementById('tab-erros');
    const tabela = document.getElementById('tabelaErros');
    if (!tab || !tabela || document.getElementById('omnixml-falhas-financeiras')) return;
    const painel = document.createElement('div');
    painel.id = 'omnixml-falhas-financeiras';
    painel.className = 'mb-6';
    painel.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div class="rounded-xl border border-rose-200 bg-rose-50 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-rose-500">Arquivos com falha</div>
          <div id="omnixml-falhas-qtd" class="text-2xl font-black text-rose-700 mt-1">0</div>
        </div>
        <div class="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-amber-600">Valor dos documentos com falha</div>
          <div id="omnixml-falhas-valor" class="text-2xl font-black text-amber-700 mt-1">R$ 0,00</div>
        </div>
        <div class="rounded-xl border border-blue-200 bg-blue-50 p-4">
          <div class="text-xs font-bold uppercase tracking-wider text-blue-600">Com chave fiscal identificada</div>
          <div id="omnixml-falhas-chave-qtd" class="text-2xl font-black text-blue-700 mt-1">0</div>
        </div>
      </div>
      <div class="overflow-x-auto rounded-xl border border-slate-200">
        <table class="w-full text-sm text-left text-slate-600">
          <thead class="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th class="p-3">Arquivo</th><th class="p-3">Nº Cupom/Nota</th><th class="p-3">Chave</th><th class="p-3 text-right">Valor</th><th class="p-3">Falha</th></tr>
          </thead>
          <tbody id="omnixml-falhas-detalhes"></tbody>
        </table>
      </div>`;
    tabela.parentElement.insertBefore(painel, tabela);
  }

  function atualizar() {
    garantirPainel();
    if (typeof dtErros === 'undefined' || !dtErros || !document.getElementById('omnixml-falhas-detalhes')) return;
    const erros = dtErros.rows().data().toArray();
    const porArquivo = new Map();
    for (const erro of erros) {
      const arquivo = erro.arquivo || erro.caminho || '';
      if (arquivo && !porArquivo.has(arquivo)) porArquivo.set(arquivo, erro);
    }
    let total = 0, comChave = 0;
    const linhas = [];
    for (const [arquivo, erro] of porArquivo) {
      const meta = metadados.get(arquivo) || metadados.get(String(arquivo).split(/[\\/]/).pop()) || {};
      const valor = Number(meta.valor || 0);
      total += valor;
      if (meta.chave) comChave++;
      const chave = meta.chave || '—';
      const chaveHtml = meta.chave
        ? `<span class="font-mono text-[11px] text-slate-600 break-all" title="${escape(meta.chave)}">${escape(meta.chave)}</span>`
        : '<span class="text-slate-400">Não identificada</span>';
      linhas.push(`<tr class="border-t border-slate-100 hover:bg-slate-50">
        <td class="p-3 font-mono text-xs font-semibold text-slate-700">${escape(String(arquivo).split(/[\\/]/).pop())}</td>
        <td class="p-3 font-mono font-bold text-slate-800">${escape(meta.numero || '—')}</td>
        <td class="p-3 max-w-[390px]">${chaveHtml}</td>
        <td class="p-3 text-right font-bold text-slate-800 whitespace-nowrap">${moeda(valor)}</td>
        <td class="p-3"><span class="inline-block px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200 text-xs font-semibold cursor-help" title="${escape(erro.motivo || '')}">${escape(motivoCurto(erro.motivo))}</span></td>
      </tr>`);
    }
    document.getElementById('omnixml-falhas-qtd').textContent = porArquivo.size.toLocaleString('pt-BR');
    document.getElementById('omnixml-falhas-valor').textContent = moeda(total);
    document.getElementById('omnixml-falhas-chave-qtd').textContent = comChave.toLocaleString('pt-BR');
    document.getElementById('omnixml-falhas-detalhes').innerHTML = linhas.join('') || '<tr><td colspan="5" class="p-4 text-center text-slate-400">Nenhuma falha fiscal encontrada.</td></tr>';
  }

  document.addEventListener('DOMContentLoaded', () => {
    garantirPainel();
    const tentar = () => {
      try {
        if (typeof dtErros !== 'undefined' && dtErros) {
          $('#tabelaErros').on('draw.dt', atualizar);
          atualizar();
          return true;
        }
      } catch (_) {}
      return false;
    };
    if (!tentar()) {
      let tentativas = 0;
      const timer = setInterval(() => { if (tentar() || ++tentativas > 60) clearInterval(timer); }, 250);
    }
  });
})();
