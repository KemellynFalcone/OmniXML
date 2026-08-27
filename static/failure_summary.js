(() => {
  const original = window.atualizarPainelDinamico;
  if (typeof original !== 'function') return;

  const chaveArquivo = erro => String(erro?.caminho || erro?.arquivo || '').trim().toLowerCase();

  function errosUnicos(erros) {
    const mapa = new Map();
    for (const erro of erros || []) {
      const chave = chaveArquivo(erro) || `erro-${mapa.size + 1}`;
      if (!mapa.has(chave)) mapa.set(chave, erro);
    }
    return Array.from(mapa.values());
  }

  function atualizarBadge(total) {
    const contador = document.getElementById('resumo-erros');
    if (contador) {
      contador.textContent = String(total);
      contador.title = `${total} arquivo${total === 1 ? '' : 's'} XML com falha`;
    }

    const faixa = document.getElementById('faixa-resumo-auditoria');
    if (faixa) {
      const rotulos = Array.from(faixa.querySelectorAll('p'));
      const rotuloFalhas = rotulos.find(el => el.textContent.trim().toLowerCase().startsWith('com falhas'));
      if (rotuloFalhas) rotuloFalhas.childNodes[0].nodeValue = 'Com Falhas (arquivos) ';
    }

    const tab = document.getElementById('tab-erros');
    if (tab) {
      let badge = document.getElementById('omnixml-total-arquivos-falha');
      if (!badge) {
        badge = document.createElement('div');
        badge.id = 'omnixml-total-arquivos-falha';
        badge.className = 'mb-4 inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700';
        const alvo = tab.querySelector('.bg-white') || tab.firstElementChild || tab;
        alvo.prepend(badge);
      }
      badge.textContent = `${total} arquivo${total === 1 ? '' : 's'} XML com falha nesta auditoria`;
    }
  }

  window.atualizarPainelDinamico = function(dados) {
    if (dados && Array.isArray(dados.erros)) {
      dados.erros = errosUnicos(dados.erros);
      dados.total_erros = dados.erros.length;
    }
    const resultado = original.apply(this, arguments);
    atualizarBadge(Number(dados?.total_erros || 0));
    return resultado;
  };
})();
