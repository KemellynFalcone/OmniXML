import re
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__, template_folder='templates', static_folder='static')

INLINE_SCRIPT_RE = re.compile(r'<script(?![^>]*\bsrc=)[^>]*>(?P<body>.*?)</script>', re.IGNORECASE | re.DOTALL)
INLINE_STYLE_RE = re.compile(r'<style[^>]*>(?P<body>.*?)</style>', re.IGNORECASE | re.DOTALL)

_RUNTIME_ESCAPE_HELPER = """
const escapeRuntimeHtml = value => String(value ?? '').replace(/[&<>\"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', "'": '&#39;'
}[char]));
""".strip()

_RUNTIME_SAFE_REPLACEMENTS = {
    "return '<span class=\"px-2.5 py-1 bg-slate-100 text-slate-700 rounded border border-slate-200 font-semibold text-[11px]\">' + data + '</span>';":
        "return '<span class=\"px-2.5 py-1 bg-slate-100 text-slate-700 rounded border border-slate-200 font-semibold text-[11px]\">' + escapeRuntimeHtml(data) + '</span>';",
    "return '<span class=\"inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-red-700 border border-red-200\">❌ ' + d + '</span>';":
        "return '<span class=\"inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-red-700 border border-red-200\">❌ ' + escapeRuntimeHtml(d) + '</span>';",
    "return '<span class=\"inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200\">⚠️ ' + d + '</span>';":
        "return '<span class=\"inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200\">⚠️ ' + escapeRuntimeHtml(d) + '</span>';",
    "{ data: 'ncm', render: function(d){return `<span class=\"font-mono font-semibold\">${d}</span>`;} }":
        "{ data: 'ncm', render: function(d){return `<span class=\"font-mono font-semibold\">${escapeRuntimeHtml(d)}</span>`;} }",
    "`<span class=\"px-2 py-0.5 rounded text-xs font-medium bg-orange-50 text-orange-700 border border-orange-200\">⚠️ ${d}</span>`":
        "`<span class=\"px-2 py-0.5 rounded text-xs font-medium bg-orange-50 text-orange-700 border border-orange-200\">⚠️ ${escapeRuntimeHtml(d)}</span>`",
    "{ data: 'ncm', render: function(d){return `<span class=\"font-mono text-blue-600 font-bold\">${d}</span>`;} }":
        "{ data: 'ncm', render: function(d){return `<span class=\"font-mono text-blue-600 font-bold\">${escapeRuntimeHtml(d)}</span>`;} }",
    "{ data: 'motivo', render: function(d) { return `<span class=\"px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium text-xs\">⚠️ ${d}</span>`; } }":
        "{ data: 'motivo', render: function(d) { return `<span class=\"px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium text-xs\">⚠️ ${escapeRuntimeHtml(d)}</span>`; } }",
    "<span>${chaveFormatada}</span>": "<span>${escapeRuntimeHtml(chaveFormatada)}</span>",
    "<button onclick=\"copiarEAbrir('${d}', '${urlSefaz}')\" class=\"text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 p-1.5 rounded transition-colors\" title=\"Copiar Chave e Abrir SEFAZ\">":
        "<button data-omnixml-sefaz-chave=\"${escapeRuntimeHtml(d)}\" data-omnixml-sefaz-url=\"${escapeRuntimeHtml(urlSefaz)}\" class=\"text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 p-1.5 rounded transition-colors\" title=\"Copiar Chave e Abrir SEFAZ\">",
}

_RUNTIME_PHASE10_REPLACEMENTS = {
    "https://cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json": "/static/datatables_ptbr_v10.json",
}

_CHART_JS_UNPINNED = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
_CHART_JS_LOCAL = '<script src="/static/vendor/chart-4.5.1.umd.min.js?v=21"></script>'
_TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
_TAILWIND_LOCAL = '<link rel="stylesheet" href="/static/tailwind_v11.css?v=1">'
_JQUERY_CDN_OLD = '<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>'
_JQUERY_LOCAL = '<script src="/static/vendor/jquery-3.7.0.min.js?v=20"></script>'
_JSZIP_CDN_OLD = '<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>'
_JSZIP_LOCAL = '<script src="/static/vendor/jszip-3.10.1.min.js?v=20"></script>'

_BROWSER_LOCAL_PROGRESS_OLD = "function progresso(a,t){const c=document.getElementById('progressContainer'),b=document.getElementById('progressBar');if(c&&b){c.style.display='block';b.style.width=`${t?Math.min(100,a/t*100):0}%`;}}"
_BROWSER_LOCAL_PROGRESS_NEW = "function progresso(a,t){const c=document.getElementById('progressContainer'),b=document.getElementById('progressBar');if(c&&b){const p=Math.max(0,Math.min(100,Math.round(t?a/t*100:0)));c.classList.add('progress-visible');for(const x of Array.from(b.classList))if(x.startsWith('progress-pct-'))b.classList.remove(x);b.classList.add(`progress-pct-${p}`);}}"
_BROWSER_LOCAL_HIDE_OLD = "setTimeout(()=>{const c=document.getElementById('progressContainer');if(c)c.style.display='none';},2500);"
_BROWSER_LOCAL_HIDE_NEW = "setTimeout(()=>document.getElementById('progressContainer')?.classList.remove('progress-visible'),2500);"

_SPED_CTA_OLD = '<button onclick="confrontarSPED()" class="bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold py-2 px-4 rounded-lg transition-all shadow-sm border border-blue-200 flex items-center gap-2 text-sm">'
_SPED_CTA_NEW = '<button onclick="confrontarSPED()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-5 rounded-lg transition-all shadow-md hover:shadow-lg flex items-center gap-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">'
_SPED_PLACEHOLDER_START = '                    <div id="placeholder-sped" class="text-center py-16">'
_SPED_RESULT_START = '                    <div id="resultado-sped" class="hidden space-y-6">'

_SPED_PREVIEW_V22 = '''                    <div id="placeholder-sped" class="sped-preview-v22">
                        <div class="sped-preview-status-row">
                            <div>
                                <span class="sped-preview-eyebrow">Confronto SPED Fiscal</span>
                                <h4 class="sped-preview-title">Veja o que será analisado antes de importar</h4>
                                <p class="sped-preview-subtitle">A estrutura abaixo é apenas uma prévia visual. Nenhum valor fiscal é calculado até você importar o arquivo SPED (.txt).</p>
                            </div>
                            <span class="sped-preview-status">Aguardando importação</span>
                        </div>

                        <div class="sped-preview-disclaimer" role="note" aria-label="Aviso sobre dados ilustrativos">
                            <strong>Prévia visual — dados ilustrativos.</strong> Os gráficos e indicadores abaixo não representam resultados da empresa.
                        </div>

                        <div class="sped-preview-grid" aria-hidden="true">
                            <section class="sped-preview-card">
                                <div class="sped-preview-card-head"><span>Divergências fiscais</span><span class="sped-preview-chip">Prévia</span></div>
                                <div class="sped-bars"><span class="sped-bar sped-bar-1"></span><span class="sped-bar sped-bar-2"></span><span class="sped-bar sped-bar-3"></span><span class="sped-bar sped-bar-4"></span><span class="sped-bar sped-bar-5"></span></div>
                                <div class="sped-preview-axis"><span>Jan</span><span>Fev</span><span>Mar</span><span>Abr</span><span>Mai</span></div>
                            </section>
                            <section class="sped-preview-card">
                                <div class="sped-preview-card-head"><span>Composição da análise</span><span class="sped-preview-chip">Prévia</span></div>
                                <div class="sped-donut"><div class="sped-donut-hole"></div></div>
                                <div class="sped-preview-legend"><span>XMLs</span><span>SPED</span><span>Divergências</span></div>
                            </section>
                            <section class="sped-preview-card">
                                <div class="sped-preview-card-head"><span>Impacto para revisão</span><span class="sped-preview-chip">Prévia</span></div>
                                <div class="sped-line-chart"><span class="sped-line-dot sped-dot-1"></span><span class="sped-line-dot sped-dot-2"></span><span class="sped-line-dot sped-dot-3"></span><span class="sped-line-dot sped-dot-4"></span><span class="sped-line-dot sped-dot-5"></span></div>
                                <div class="sped-preview-axis"><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span></div>
                            </section>
                        </div>

                        <div class="sped-next-steps">
                            <div class="sped-next-step"><span class="sped-step-number">1</span><div><strong>Importe o SPED</strong><small>Selecione o arquivo .txt da escrituração fiscal.</small></div></div>
                            <div class="sped-next-step"><span class="sped-step-number">2</span><div><strong>Confronte com os XMLs</strong><small>O OmniXML compara os valores já apurados no navegador.</small></div></div>
                            <div class="sped-next-step"><span class="sped-step-number">3</span><div><strong>Revise as diferenças</strong><small>Abra o detalhamento nota a nota somente quando houver divergências.</small></div></div>
                        </div>
                    </div>

'''


def _endurecer_runtime_dashboard(script):
    """Neutraliza dados dinâmicos e elimina chamadas externas evitáveis no runtime."""
    hardened = script
    missing = []
    for vulnerable, safe in _RUNTIME_SAFE_REPLACEMENTS.items():
        if vulnerable not in hardened:
            missing.append(vulnerable[:80])
            continue
        hardened = hardened.replace(vulnerable, safe)
    if missing:
        raise RuntimeError(f'Renderizadores esperados da Fase 8 não encontrados: {missing}')

    phase10_missing = []
    for external, local in _RUNTIME_PHASE10_REPLACEMENTS.items():
        if external not in hardened:
            phase10_missing.append(external)
            continue
        hardened = hardened.replace(external, local)
    if phase10_missing:
        raise RuntimeError(f'Dependências esperadas da Fase 10 não encontradas: {phase10_missing}')
    return f'{_RUNTIME_ESCAPE_HELPER}\n\n{hardened}'


def _endurecer_ativos_externos(html):
    """Localiza Chart.js/jQuery/JSZip e substitui Tailwind pelo CSS local."""
    obrigatorios = (
        (_CHART_JS_UNPINNED, 'Importação não versionada do Chart.js não encontrada.'),
        (_TAILWIND_CDN, 'Importação do Tailwind CDN não encontrada.'),
        (_JQUERY_CDN_OLD, 'Importação histórica do jQuery 3.7.0 não encontrada.'),
        (_JSZIP_CDN_OLD, 'Importação histórica do JSZip 3.10.1 não encontrada.'),
    )
    for marcador, erro in obrigatorios:
        if marcador not in html:
            raise RuntimeError(erro)

    html = html.replace(_CHART_JS_UNPINNED, _CHART_JS_LOCAL, 1)
    html = html.replace(_TAILWIND_CDN, _TAILWIND_LOCAL, 1)
    html = html.replace(_JQUERY_CDN_OLD, _JQUERY_LOCAL, 1)
    return html.replace(_JSZIP_CDN_OLD, _JSZIP_LOCAL, 1)


def _aprimorar_sped_preview_v22(html):
    """Troca somente o estado vazio do SPED por uma prévia orientada à ação."""
    if _SPED_CTA_OLD not in html:
        raise RuntimeError('CTA histórico do SPED não encontrado.')
    start = html.find(_SPED_PLACEHOLDER_START)
    end = html.find(_SPED_RESULT_START, start)
    if start < 0 or end < 0:
        raise RuntimeError('Placeholder histórico do SPED não encontrado.')
    html = html.replace(_SPED_CTA_OLD, _SPED_CTA_NEW, 1)
    return html[:start] + _SPED_PREVIEW_V22 + html[end:]


def _css_progresso_sem_inline():
    regras = ['.progress-container.progress-visible { display: block; }']
    regras.extend(f'.progress-bar.progress-pct-{pct} {{ width: {pct}%; }}' for pct in range(101))
    return '\n'.join(regras)


def _css_sped_preview_v22():
    return '''
.sped-preview-v22 { padding: 0.25rem 0 1rem; text-align: left; }
.sped-preview-status-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 1.5rem; padding: 0.25rem 0 1.25rem; }
.sped-preview-eyebrow { display: block; color: #2563eb; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.35rem; }
.sped-preview-title { color: #0f172a; font-size: 1.15rem; line-height: 1.45; font-weight: 800; }
.sped-preview-subtitle { color: #64748b; font-size: 0.875rem; line-height: 1.55; max-width: 48rem; margin-top: 0.35rem; }
.sped-preview-status { flex-shrink: 0; background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; border-radius: 9999px; padding: 0.45rem 0.8rem; font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
.sped-preview-disclaimer { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; border-radius: 0.75rem; padding: 0.75rem 1rem; font-size: 0.8rem; margin-bottom: 1rem; }
.sped-preview-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
.sped-preview-card { min-height: 11rem; border: 1px solid #e2e8f0; border-radius: 0.85rem; background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); padding: 1rem; overflow: hidden; }
.sped-preview-card-head { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; color: #334155; font-size: 0.78rem; font-weight: 800; }
.sped-preview-chip { color: #94a3b8; background: #f1f5f9; border-radius: 9999px; padding: 0.2rem 0.45rem; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.05em; }
.sped-bars { height: 6.2rem; display: flex; align-items: flex-end; justify-content: space-around; gap: 0.55rem; padding: 0.8rem 0.3rem 0; border-bottom: 1px solid #e2e8f0; }
.sped-bar { width: 1.5rem; border-radius: 0.3rem 0.3rem 0 0; background: #cbd5e1; }
.sped-bar-1 { height: 34%; } .sped-bar-2 { height: 56%; background: #93c5fd; } .sped-bar-3 { height: 43%; } .sped-bar-4 { height: 72%; background: #60a5fa; } .sped-bar-5 { height: 86%; background: #3b82f6; }
.sped-preview-axis { display: flex; justify-content: space-around; gap: 0.4rem; padding-top: 0.45rem; color: #94a3b8; font-size: 0.62rem; }
.sped-donut { width: 6.5rem; height: 6.5rem; margin: 0.8rem auto 0.5rem; border-radius: 50%; background: conic-gradient(#3b82f6 0 38%, #94a3b8 38% 70%, #e2e8f0 70% 100%); display: flex; align-items: center; justify-content: center; }
.sped-donut-hole { width: 3.45rem; height: 3.45rem; border-radius: 50%; background: #ffffff; border: 1px solid #f1f5f9; }
.sped-preview-legend { display: flex; justify-content: center; gap: 0.7rem; color: #64748b; font-size: 0.62rem; }
.sped-line-chart { position: relative; height: 6.9rem; margin-top: 0.45rem; border-bottom: 1px solid #e2e8f0; background: linear-gradient(165deg, transparent 0 42%, #bfdbfe 42% 44%, transparent 44% 53%, #60a5fa 53% 55%, transparent 55% 100%); }
.sped-line-dot { position: absolute; width: 0.52rem; height: 0.52rem; background: #2563eb; border: 2px solid white; box-shadow: 0 0 0 1px #93c5fd; border-radius: 50%; }
.sped-dot-1 { left: 7%; bottom: 20%; } .sped-dot-2 { left: 28%; bottom: 34%; } .sped-dot-3 { left: 49%; bottom: 31%; } .sped-dot-4 { left: 70%; bottom: 55%; } .sped-dot-5 { right: 7%; bottom: 70%; }
.sped-next-steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.75rem; margin-top: 1rem; }
.sped-next-step { display: flex; gap: 0.7rem; align-items: flex-start; border: 1px solid #e2e8f0; background: #ffffff; border-radius: 0.75rem; padding: 0.8rem; }
.sped-step-number { width: 1.65rem; height: 1.65rem; flex: 0 0 1.65rem; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; background: #dbeafe; color: #1d4ed8; font-size: 0.72rem; font-weight: 900; }
.sped-next-step strong { display: block; color: #334155; font-size: 0.78rem; }
.sped-next-step small { display: block; color: #64748b; font-size: 0.7rem; line-height: 1.35; margin-top: 0.15rem; }
@media (max-width: 900px) { .sped-preview-grid, .sped-next-steps { grid-template-columns: 1fr; } .sped-preview-status-row { flex-direction: column; } }
'''.strip()


def _separar_estilo_dashboard(html):
    """Externaliza o CSS próprio do template e inclui progresso/preview sem style attributes."""
    matches = list(INLINE_STYLE_RE.finditer(html))
    if len(matches) != 1:
        raise RuntimeError(f'Esperado exatamente 1 bloco de estilo próprio; encontrados {len(matches)}.')
    match = matches[0]
    css = match.group('body').strip() + '\n\n' + _css_progresso_sem_inline() + '\n\n' + _css_sped_preview_v22() + '\n'
    external = '<link rel="stylesheet" href="/static/dashboard_style_v9.css?v=1">'
    safe_html = html[:match.start()] + external + html[match.end():]
    return safe_html, css


def _separar_runtime_dashboard(html):
    """Remove o último bloco JS inline do dashboard e devolve HTML + runtime externo."""
    matches = list(INLINE_SCRIPT_RE.finditer(html))
    if not matches:
        raise RuntimeError('Runtime inline principal do dashboard não encontrado.')
    match = matches[-1]
    script = _endurecer_runtime_dashboard(match.group('body').strip() + '\n')
    external = '<script src="/static/dashboard_runtime_v6.js?v=1&phase=8"></script>'
    safe_html = html[:match.start()] + external + html[match.end():]
    return safe_html, script


def _browser_local_com_cnpj_alfanumerico():
    """Adapta CNPJ e remove styles inline do progresso do processador local."""
    source = Path(app.root_path, 'static', 'browser_local_v2.js').read_text(encoding='utf-8')
    old = "const docId=el=>txt(child(el,'CNPJ'))||txt(child(el,'CPF'))||'';"
    new = (
        "const docId=el=>{const cnpj=txt(child(el,'CNPJ'));"
        "if(cnpj)return window.__omnixmlCnpj?.normalizar(cnpj)||String(cnpj).trim().toUpperCase();"
        "return txt(child(el,'CPF'))||'';};"
    )
    if old not in source:
        raise RuntimeError('Ponto de normalização de CNPJ do processador local não encontrado.')
    source = source.replace(old, new, 1)
    if _BROWSER_LOCAL_PROGRESS_OLD not in source or _BROWSER_LOCAL_HIDE_OLD not in source:
        raise RuntimeError('Pontos de estilo inline do progresso não encontrados.')
    source = source.replace(_BROWSER_LOCAL_PROGRESS_OLD, _BROWSER_LOCAL_PROGRESS_NEW, 1)
    return source.replace(_BROWSER_LOCAL_HIDE_OLD, _BROWSER_LOCAL_HIDE_NEW, 1)


def _inutilizacao_com_cnpj_alfanumerico():
    """Normaliza CNPJ de inutilizações para a mesma chave textual usada nas notas."""
    source = Path(app.root_path, 'static', 'inutilization_capture.js').read_text(encoding='utf-8')
    old = "cnpj: valor('CNPJ'),"
    new = "cnpj: window.__omnixmlCnpj?.normalizar(valor('CNPJ')) || valor('CNPJ'),"
    if old not in source:
        raise RuntimeError('Ponto de CNPJ da inutilização não encontrado.')
    return source.replace(old, new, 1)


@app.before_request
def servir_compatibilidade_cnpj_alfanumerico():
    """Preserva URLs históricas dos scripts enquanto injeta compatibilidade e hardening."""
    if request.path == '/static/browser_local_v2.js':
        return Response(_browser_local_com_cnpj_alfanumerico(), mimetype='application/javascript')
    if request.path == '/static/inutilization_capture.js':
        return Response(_inutilizacao_com_cnpj_alfanumerico(), mimetype='application/javascript')
    return None


@app.after_request
def aplicar_cabecalhos_seguranca(response):
    """Camada de hardening HTTP para a interface pública do OmniXML."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "frame-src 'none'; "
        "form-action 'self'; "
        "media-src 'none'; "
        "manifest-src 'self'; "
        "script-src 'self' https://cdn.datatables.net; "
        "style-src 'self' https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "style-src-elem 'self' https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "style-src-attr 'none'; "
        "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "worker-src 'self' blob:"
    )
    response.headers['Content-Security-Policy-Report-Only'] = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "script-src 'self' https://cdn.datatables.net; "
        "style-src 'self' https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "style-src-elem 'self' https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "style-src-attr 'none'"
    )
    if response.is_json or response.mimetype in {'text/html', 'application/json', 'application/javascript', 'text/javascript', 'text/css'}:
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/')
def index():
    html = _endurecer_ativos_externos(render_template('dashboard.html'))
    html = _aprimorar_sped_preview_v22(html)
    html, _ = _separar_estilo_dashboard(html)
    html, _ = _separar_runtime_dashboard(html)
    ponte = (
        '<script src="/static/browser_security_v2.js?v=1&phase=7"></script>'
        '<script src="/static/browser_security_v3.js?v=1"></script>'
        '<script src="/static/safe_renderers_v8.js?v=1"></script>'
        '<script src="/static/cnpj_alfanumerico_v1.js?v=1"></script>'
        '<script src="/static/failure_table_v2.js?v=2"></script>'
        '<script src="/static/browser_validation.js?v=1"></script>'
        '<script src="/static/failure_summary.js?v=1"></script>'
        '<script src="/static/inutilization_capture.js?v=1&cnpj=1"></script>'
        '<script src="/static/closing_diagnosis_v2.js?v=3"></script>'
        '<script src="/static/browser_local_v2.js?v=2&cnpj=1&style=13"></script>'
        '<script src="/static/inline_handler_bridge_v5.js?v=1"></script>'
    )
    return Response(html.replace('</body>', f'{ponte}</body>'), mimetype='text/html')


@app.get('/static/dashboard_runtime_v6.js')
def dashboard_runtime_v6():
    _, script = _separar_runtime_dashboard(render_template('dashboard.html'))
    return Response(script, mimetype='application/javascript')


@app.get('/static/dashboard_style_v9.css')
def dashboard_style_v9():
    _, css = _separar_estilo_dashboard(render_template('dashboard.html'))
    return Response(css, mimetype='text/css')


@app.get('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'OmniXML Web',
        'processing': 'browser-local',
        'classification': 'cnpj-participants',
        'fiscal_validation': 'authorization-structure',
        'failure_summary': 'unique-files',
        'failure_table': 'v2-key-value-reason',
        'closing_diagnosis': 'sequence-with-inutilization-reconciliation',
        'inutilization_reconciliation': 'homologated-cstat-102',
        'security_headers': 'hardening-v1-csp-phase3',
        'browser_security': 'xss-display-escape-limits-dom-navigation-guards-v3',
        'safe_dom': 'closing-diagnosis-and-failure-table-v4',
        'inline_handlers': 'external-allowlisted-bridge-v5',
        'dashboard_runtime': 'externalized-v6',
        'runtime_sinks': 'all-primary-datatables-display-escaped-v7',
        'safe_renderers': 'escaped-dynamic-markup-and-data-sefaz-v8',
        'style_csp': 'own-css-external-strict-report-only-v9',
        'external_assets': 'local-datatables-i18n-pinned-chartjs-v10',
        'tailwind_assets': 'compiled-local-css-v11',
        'style_csp_enforcement': 'strict-elements-and-attrs-v18',
        'style_attr_app': 'class-driven-progress-v13',
        'style_attr_probe': 'validated-and-retired-v18',
        'script_assets': 'local-jquery-jszip-chartjs-v21',
        'sped_empty_state': 'preview-action-guidance-v22',
        'cnpj_support': 'alphanumeric-14-rfb-v1',
        'csp_migration': 'strict-script-policy-report-only',
        'csp_enforcement': 'strict-script-policy-enforced-v6',
        'xml_upload': False,
    })
