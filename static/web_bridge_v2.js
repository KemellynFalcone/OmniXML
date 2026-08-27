(() => {
    let consultaAtual = null;
    const MAX_LOTE_BYTES = 25 * 1024 * 1024;
    const MAX_LOTE_ARQUIVOS = 100;

    const htmlModal = `
    <div id="omnixml-web-modal" class="fixed inset-0 z-[9999] hidden items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
      <div class="w-full max-w-2xl rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden">
        <div class="px-6 py-5 border-b border-slate-200 flex items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-black text-slate-800">Importar documentos fiscais</h2>
            <p class="text-sm text-slate-500 mt-1">Escolha XMLs, uma pasta inteira ou ZIP. O envio é dividido em lotes e nada fica salvo permanentemente.</p>
          </div>
          <button id="omnixml-web-fechar" class="text-slate-400 hover:text-slate-700 text-xl leading-none">×</button>
        </div>
        <div class="p-6 grid md:grid-cols-3 gap-4">
          <button id="omnixml-web-arquivos" class="rounded-xl border border-blue-200 bg-blue-50 hover:bg-blue-100 p-5 text-left transition">
            <div class="font-bold text-blue-700">XMLs / ZIP</div>
            <div class="text-xs text-slate-500 mt-1">Selecione vários arquivos.</div>
          </button>
          <button id="omnixml-web-pasta" class="rounded-xl border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 p-5 text-left transition">
            <div class="font-bold text-emerald-700">Pasta inteira</div>
            <div class="text-xs text-slate-500 mt-1">Inclui XMLs das subpastas.</div>
          </button>
          <button id="omnixml-web-cancelar" class="rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 p-5 text-left transition">
            <div class="font-bold text-slate-700">Cancelar</div>
            <div class="text-xs text-slate-500 mt-1">Voltar ao dashboard.</div>
          </button>
        </div>
        <div class="px-6 pb-6 text-xs text-slate-400">O navegador envia lotes menores para evitar o limite de 200 MB por requisição.</div>
      </div>
    </div>
    <input id="omnixml-web-input-arquivos" class="hidden" type="file" multiple accept=".xml,.zip,text/xml,application/xml,application/zip">
    <input id="omnixml-web-input-pasta" class="hidden" type="file" multiple webkitdirectory directory accept=".xml,text/xml,application/xml">
    `;

    function garantirControles() {
        if (document.getElementById('omnixml-web-modal')) return;
        document.body.insertAdjacentHTML('beforeend', htmlModal);
        const modal = document.getElementById('omnixml-web-modal');
        const fechar = () => { modal.classList.add('hidden'); modal.classList.remove('flex'); };
        const abrir = () => { modal.classList.remove('hidden'); modal.classList.add('flex'); };

        document.getElementById('omnixml-web-fechar').onclick = fechar;
        document.getElementById('omnixml-web-cancelar').onclick = fechar;
        document.getElementById('omnixml-web-arquivos').onclick = () => document.getElementById('omnixml-web-input-arquivos').click();
        document.getElementById('omnixml-web-pasta').onclick = () => document.getElementById('omnixml-web-input-pasta').click();
        document.getElementById('omnixml-web-input-arquivos').addEventListener('change', e => processarArquivos(e.target.files, fechar));
        document.getElementById('omnixml-web-input-pasta').addEventListener('change', e => processarArquivos(e.target.files, fechar));
        window.iniciarProcessamento = abrir;
    }

    function status(html) {
        const el = document.getElementById('statusAuditoria');
        if (el) el.innerHTML = html;
    }

    function progresso(valor, total) {
        const container = document.getElementById('progressContainer');
        const bar = document.getElementById('progressBar');
        if (!container || !bar) return;
        container.style.display = 'block';
        const pct = total ? Math.min(100, (valor / total) * 100) : 0;
        bar.style.width = pct + '%';
    }

    function dividirEmLotes(files) {
        const lotes = [];
        let atual = [];
        let bytes = 0;
        for (const file of files) {
            const excede = atual.length && (bytes + file.size > MAX_LOTE_BYTES || atual.length >= MAX_LOTE_ARQUIVOS);
            if (excede) {
                lotes.push(atual);
                atual = [];
                bytes = 0;
            }
            atual.push(file);
            bytes += file.size;
        }
        if (atual.length) lotes.push(atual);
        return lotes;
    }

    function xhrJson(method, url, formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open(method, url, true);
            xhr.responseType = 'json';
            if (xhr.upload && onProgress) {
                xhr.upload.onprogress = event => {
                    if (event.lengthComputable) onProgress(event.loaded, event.total);
                };
            }
            xhr.onload = () => {
                const payload = xhr.response || {};
                if (xhr.status >= 200 && xhr.status < 300) resolve(payload);
                else reject(new Error(payload.mensagem || `Falha no envio (${xhr.status}).`));
            };
            xhr.onerror = () => reject(new Error('Falha de rede durante o envio dos arquivos.'));
            xhr.send(formData);
        });
    }

    async function processarArquivos(fileList, fecharModal) {
        const files = Array.from(fileList || []).filter(f => /\.(xml|zip)$/i.test(f.name));
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

            status('<span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span> Preparando consulta temporária...');
            const criarResp = await fetch('/api/v2/consultas', {method: 'POST'});
            const criar = await criarResp.json();
            if (!criarResp.ok) throw new Error(criar.mensagem || 'Falha ao iniciar consulta.');
            consultaAtual = criar.consulta_id;

            const lotes = dividirEmLotes(files);
            const totalBytes = files.reduce((s, f) => s + f.size, 0);
            let bytesConcluidos = 0;
            let arquivosEnviados = 0;

            for (let i = 0; i < lotes.length; i++) {
                const lote = lotes[i];
                const form = new FormData();
                lote.forEach(file => form.append('arquivos', file, file.webkitRelativePath || file.name));
                const loteBytes = lote.reduce((s, f) => s + f.size, 0);

                status(`<span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span> Enviando lote ${i + 1} de ${lotes.length} — ${arquivosEnviados} de ${files.length} arquivos enviados...`);

                await xhrJson('POST', `/api/v2/consultas/${consultaAtual}/arquivos`, form, (loaded) => {
                    progresso(bytesConcluidos + loaded, totalBytes);
                    const pct = totalBytes ? Math.round(((bytesConcluidos + loaded) / totalBytes) * 100) : 0;
                    status(`<span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span> Upload: ${pct}% — lote ${i + 1}/${lotes.length}`);
                });

                bytesConcluidos += loteBytes;
                arquivosEnviados += lote.length;
                progresso(bytesConcluidos, totalBytes);
            }

            status(`<span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span> Upload concluído. Processando ${files.length} arquivos...`);
            let resumo = {processados: 0, total: files.length};
            progresso(0, resumo.total);

            while (resumo.processados < resumo.total) {
                const resp = await fetch(`/api/consultas/${consultaAtual}/processar?limite=100`, {method: 'POST'});
                const lote = await resp.json();
                if (!resp.ok) throw new Error(lote.mensagem || 'Falha durante o processamento.');
                resumo = lote.resumo;
                progresso(resumo.processados, resumo.total);
                const pct = resumo.total ? Math.round((resumo.processados / resumo.total) * 100) : 0;
                status(`<span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span> Processamento: ${pct}% — ${resumo.processados} de ${resumo.total} XMLs`);
            }

            status('<span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span> Montando dashboard fiscal...');
            const dashResp = await fetch(`/api/consultas/${consultaAtual}/dashboard`);
            const dados = await dashResp.json();
            if (!dashResp.ok) throw new Error(dados.mensagem || 'Falha ao montar o dashboard.');
            aplicarDashboard(dados);
        } catch (error) {
            console.error(error);
            status(`<span class="w-2 h-2 rounded-full bg-red-500"></span> ${escapeHtml(error.message)}`);
            alert(error.message);
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = 'Importar e Auditar XMLs'; }
            setTimeout(() => {
                const container = document.getElementById('progressContainer');
                if (container) container.style.display = 'none';
            }, 3000);
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
        const notaEmpresa = (dados.notas || []).find(n => n.operacao === 'Saída' && n.emitente && n.emitente !== 'Desconhecido')
            || (dados.notas || []).find(n => n.emitente && n.emitente !== 'Desconhecido');
        if (notaEmpresa) nomeEmpresa = notaEmpresa.emitente;
        const header = document.getElementById('nomeEmpresaHeader');
        if (header) header.innerText = nomeEmpresa;

        status(`<span class="w-2 h-2 rounded-full bg-emerald-500"></span> Auditoria concluída (${dados.total_lidos || 0} arquivos lidos)`);
        document.getElementById('faixa-resumo-auditoria')?.classList.remove('hidden');
        document.getElementById('btnTrocarCliente')?.classList.remove('hidden');
        document.getElementById('btnExportarGeral')?.classList.remove('hidden');
        document.getElementById('card-boas-vindas')?.classList.add('hidden');
    }

    window.limparESairCliente = async function() {
        if (!confirm('Deseja limpar a consulta atual e iniciar uma nova?')) return;
        if (consultaAtual) {
            try { await fetch(`/api/consultas/${consultaAtual}`, {method: 'DELETE'}); } catch (_) {}
        }
        consultaAtual = null;
        location.reload();
    };

    const oldExportar = window.exportarRelatorioGeral;
    window.exportarRelatorioGeral = function() {
        if (consultaAtual) {
            window.open(`/api/consultas/${consultaAtual}/relatorio.csv`, '_blank');
            return;
        }
        if (oldExportar) oldExportar();
    };

    window.confrontarSPED = function() {
        alert('O upload web do SPED Fiscal será a próxima etapa. O módulo visual foi preservado.');
    };
    window.importarPisCofins = function() {
        alert('O upload web da EFD-Contribuições será a próxima etapa. O módulo visual foi preservado.');
    };

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', garantirControles);
    else garantirControles();
})();
