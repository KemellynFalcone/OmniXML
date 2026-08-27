(() => {
    let consultaAtual = null;
    const MAX_BATCH_BYTES = 40 * 1024 * 1024;
    const MAX_FILES_PER_BATCH = 200;

    const modalHtml = `
    <div id="omnixml-v3-modal" class="fixed inset-0 z-[9999] hidden items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
      <div class="w-full max-w-2xl rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden">
        <div class="px-6 py-5 border-b border-slate-200 flex justify-between gap-4">
          <div>
            <h2 class="text-xl font-black text-slate-800">Importar documentos fiscais</h2>
            <p class="text-sm text-slate-500 mt-1">Arquivos grandes são enviados em lotes pequenos e processados imediatamente.</p>
          </div>
          <button id="omnixml-v3-fechar" class="text-slate-400 hover:text-slate-700 text-xl">×</button>
        </div>
        <div class="p-6 grid md:grid-cols-3 gap-4">
          <button id="omnixml-v3-arquivos" class="rounded-xl border border-blue-200 bg-blue-50 hover:bg-blue-100 p-5 text-left">
            <div class="font-bold text-blue-700">XMLs / ZIP</div>
            <div class="text-xs text-slate-500 mt-1">Selecione vários arquivos.</div>
          </button>
          <button id="omnixml-v3-pasta" class="rounded-xl border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 p-5 text-left">
            <div class="font-bold text-emerald-700">Pasta inteira</div>
            <div class="text-xs text-slate-500 mt-1">Inclui XMLs das subpastas.</div>
          </button>
          <button id="omnixml-v3-cancelar" class="rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 p-5 text-left">
            <div class="font-bold text-slate-700">Cancelar</div>
            <div class="text-xs text-slate-500 mt-1">Voltar ao dashboard.</div>
          </button>
        </div>
        <div class="px-6 pb-6 text-xs text-slate-400">Nenhum XML fica armazenado permanentemente. Cada lote é processado e removido antes do próximo.</div>
      </div>
    </div>
    <input id="omnixml-v3-input-arquivos" class="hidden" type="file" multiple accept=".xml,.zip,text/xml,application/xml,application/zip">
    <input id="omnixml-v3-input-pasta" class="hidden" type="file" multiple webkitdirectory directory accept=".xml,text/xml,application/xml">
    `;

    function status(texto, cor = 'blue') {
        const el = document.getElementById('statusAuditoria');
        if (el) el.innerHTML = `<span class="w-2 h-2 rounded-full bg-${cor}-500 ${cor === 'blue' ? 'animate-pulse' : ''}"></span> ${texto}`;
    }

    function progresso(percentual) {
        const container = document.getElementById('progressContainer');
        const bar = document.getElementById('progressBar');
        if (!container || !bar) return;
        container.style.display = 'block';
        bar.style.width = `${Math.max(0, Math.min(100, percentual))}%`;
    }

    function montarLotes(files) {
        const lotes = [];
        let atual = [];
        let bytes = 0;
        for (const file of files) {
            const tamanho = Number(file.size || 0);
            if (tamanho > 60 * 1024 * 1024) {
                throw new Error(`${file.name}: arquivo acima de 60 MB. Se for ZIP, extraia e selecione a pasta.`);
            }
            if (atual.length && (bytes + tamanho > MAX_BATCH_BYTES || atual.length >= MAX_FILES_PER_BATCH)) {
                lotes.push(atual);
                atual = [];
                bytes = 0;
            }
            atual.push(file);
            bytes += tamanho;
        }
        if (atual.length) lotes.push(atual);
        return lotes;
    }

    function enviarLote(consultaId, lote, bytesConcluidos, bytesTotais, indice, totalLotes) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `/api/v3/consultas/${consultaId}/uploads`);
            xhr.responseType = 'json';
            xhr.upload.onprogress = event => {
                if (!event.lengthComputable) return;
                const enviadosAgora = event.loaded;
                const pct = bytesTotais ? ((bytesConcluidos + enviadosAgora) / bytesTotais) * 100 : 0;
                progresso(pct);
                status(`Upload: ${pct.toFixed(0)}% — lote ${indice + 1} de ${totalLotes}`);
            };
            xhr.onload = () => {
                const payload = xhr.response || {};
                if (xhr.status >= 200 && xhr.status < 300) resolve(payload);
                else reject(new Error(payload.mensagem || `Falha no lote ${indice + 1}.`));
            };
            xhr.onerror = () => reject(new Error(`Falha de rede no lote ${indice + 1}.`));
            const form = new FormData();
            lote.forEach(file => form.append('arquivos', file, file.webkitRelativePath || file.name));
            xhr.send(form);
        });
    }

    async function processarAteAtual(consultaId, totalAtual, loteAtual, totalLotes) {
        let processados = 0;
        while (processados < totalAtual) {
            const resp = await fetch(`/api/consultas/${consultaId}/processar?limite=100`, {method: 'POST'});
            const payload = await resp.json();
            if (!resp.ok) throw new Error(payload.mensagem || 'Falha durante o processamento.');
            processados = Number(payload.resumo?.processados || 0);
            const pct = totalAtual ? (processados / totalAtual) * 100 : 100;
            progresso(pct);
            status(`Processando lote ${loteAtual} de ${totalLotes}: ${processados} de ${totalAtual} XMLs`);
        }
    }

    async function iniciarConsultaIncremental(fileList, fecharModal) {
        const files = Array.from(fileList || []).filter(file => /\.(xml|zip)$/i.test(file.name));
        if (!files.length) {
            alert('Nenhum XML ou ZIP foi selecionado.');
            return;
        }

        fecharModal();
        const btn = document.getElementById('btnProcessarDash');
        if (btn) { btn.disabled = true; btn.innerHTML = 'Processando...'; }

        try {
            if (consultaAtual) {
                try { await fetch(`/api/consultas/${consultaAtual}`, {method: 'DELETE'}); } catch (_) {}
            }

            const criarResp = await fetch('/api/v3/consultas', {method: 'POST'});
            const criar = await criarResp.json();
            if (!criarResp.ok) throw new Error(criar.mensagem || 'Falha ao iniciar a consulta.');
            consultaAtual = criar.consulta_id;

            const lotes = montarLotes(files);
            const bytesTotais = files.reduce((s, f) => s + Number(f.size || 0), 0);
            let bytesConcluidos = 0;
            let totalServidor = 0;

            for (let i = 0; i < lotes.length; i++) {
                const lote = lotes[i];
                status(`Preparando lote ${i + 1} de ${lotes.length}...`);
                const respostaLote = await enviarLote(consultaAtual, lote, bytesConcluidos, bytesTotais, i, lotes.length);
                bytesConcluidos += lote.reduce((s, f) => s + Number(f.size || 0), 0);
                totalServidor = Number(respostaLote.resumo?.total || totalServidor);

                // Processa e remove o lote antes de enviar o próximo, reduzindo uso de disco/RAM.
                await processarAteAtual(consultaAtual, totalServidor, i + 1, lotes.length);
            }

            const fimResp = await fetch(`/api/v3/consultas/${consultaAtual}/finalizar-upload`, {method: 'POST'});
            const fim = await fimResp.json();
            if (!fimResp.ok) throw new Error(fim.mensagem || 'Falha ao finalizar upload.');

            progresso(100);
            status('Montando dashboard fiscal...');
            const dashResp = await fetch(`/api/consultas/${consultaAtual}/dashboard`);
            const dados = await dashResp.json();
            if (!dashResp.ok) throw new Error(dados.mensagem || 'Falha ao montar o dashboard.');
            aplicarDashboard(dados);
        } catch (error) {
            console.error(error);
            status(escapeHtml(error.message), 'red');
            alert(error.message);
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = 'Importar e Auditar XMLs'; }
            setTimeout(() => {
                const container = document.getElementById('progressContainer');
                if (container) container.style.display = 'none';
            }, 3500);
        }
    }

    function aplicarDashboard(dados) {
        xmlNotasGlobais = dados.notas || [];
        dtCancelados.clear().rows.add((dados.notas || []).filter(n => n.status && n.status.includes('Cancelado'))).draw();
        dtNFCe.clear().rows.add((dados.notas || []).filter(n => n.tipo && n.tipo.includes('NFC-e'))).draw();
        dtNFe.clear().rows.add((dados.notas || []).filter(n => n.tipo && n.tipo.includes('NF-e'))).draw();
        dtCFOP.clear().rows.add(dados.cfop || []).draw();
        dtCST.clear().rows.add(dados.cst || []).draw();
        dtSerie.clear().rows.add(dados.serie || []).draw();
        dtAuditoria.clear().rows.add(dados.auditoria || []).draw();
        dtProdutos.clear().rows.add(dados.produtos || []).draw();
        dtErros.clear().rows.add(dados.erros || []).draw();
        atualizarPainelDinamico(dados);
        renderizarGraficos(dados.cfop || [], dados.cst || [], dados.diario || []);

        let nomeEmpresa = 'Empresa não identificada';
        const notaEmpresa = (dados.notas || []).find(n => n.operacao === 'Saída' && (n.emitente_nome || n.emitente));
        if (notaEmpresa) nomeEmpresa = notaEmpresa.emitente_nome || notaEmpresa.emitente;
        const header = document.getElementById('nomeEmpresaHeader');
        if (header) header.innerText = nomeEmpresa;

        status(`Auditoria concluída (${dados.total_lidos || 0} arquivos lidos)`, 'emerald');
        document.getElementById('faixa-resumo-auditoria')?.classList.remove('hidden');
        document.getElementById('btnTrocarCliente')?.classList.remove('hidden');
        document.getElementById('btnExportarGeral')?.classList.remove('hidden');
        document.getElementById('card-boas-vindas')?.classList.add('hidden');
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    function instalar() {
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = document.getElementById('omnixml-v3-modal');
        const abrir = () => { modal.classList.remove('hidden'); modal.classList.add('flex'); };
        const fechar = () => { modal.classList.add('hidden'); modal.classList.remove('flex'); };

        document.getElementById('omnixml-v3-fechar').onclick = fechar;
        document.getElementById('omnixml-v3-cancelar').onclick = fechar;
        document.getElementById('omnixml-v3-arquivos').onclick = () => document.getElementById('omnixml-v3-input-arquivos').click();
        document.getElementById('omnixml-v3-pasta').onclick = () => document.getElementById('omnixml-v3-input-pasta').click();
        document.getElementById('omnixml-v3-input-arquivos').addEventListener('change', e => iniciarConsultaIncremental(e.target.files, fechar));
        document.getElementById('omnixml-v3-input-pasta').addEventListener('change', e => iniciarConsultaIncremental(e.target.files, fechar));
        window.iniciarProcessamento = abrir;

        window.limparESairCliente = async function() {
            if (!confirm('Deseja limpar a consulta atual e iniciar uma nova?')) return;
            if (consultaAtual) {
                try { await fetch(`/api/consultas/${consultaAtual}`, {method: 'DELETE'}); } catch (_) {}
            }
            location.reload();
        };

        window.exportarRelatorioGeral = function() {
            if (consultaAtual) window.open(`/api/consultas/${consultaAtual}/relatorio.csv`, '_blank');
        };

        window.confrontarSPED = function() { alert('O upload web do SPED Fiscal será a próxima etapa.'); };
        window.importarPisCofins = function() { alert('O upload web da EFD-Contribuições será a próxima etapa.'); };
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', instalar);
    else instalar();
})();
