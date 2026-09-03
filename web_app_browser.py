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


def _endurecer_runtime_dashboard(script):
    """Neutraliza dados dinâmicos em renderizadores HTML legados antes de servir o runtime."""
    hardened = script
    missing = []
    for vulnerable, safe in _RUNTIME_SAFE_REPLACEMENTS.items():
        if vulnerable not in hardened:
            missing.append(vulnerable[:80])
            continue
        hardened = hardened.replace(vulnerable, safe)
    if missing:
        raise RuntimeError(f'Renderizadores esperados da Fase 8 não encontrados: {missing}')
    return f'{_RUNTIME_ESCAPE_HELPER}\n\n{hardened}'


def _separar_estilo_dashboard(html):
    """Externaliza o CSS próprio do template para preparar CSP de estilos estrita."""
    matches = list(INLINE_STYLE_RE.finditer(html))
    if len(matches) != 1:
        raise RuntimeError(f'Esperado exatamente 1 bloco de estilo próprio; encontrados {len(matches)}.')
    match = matches[0]
    css = match.group('body').strip() + '\n'
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
    """Adapta o processador local para comparar CNPJ numérico e alfanumérico como texto normalizado."""
    source = Path(app.root_path, 'static', 'browser_local_v2.js').read_text(encoding='utf-8')
    old = "const docId=el=>txt(child(el,'CNPJ'))||txt(child(el,'CPF'))||'';"
    new = (
        "const docId=el=>{const cnpj=txt(child(el,'CNPJ'));"
        "if(cnpj)return window.__omnixmlCnpj?.normalizar(cnpj)||String(cnpj).trim().toUpperCase();"
        "return txt(child(el,'CPF'))||'';};"
    )
    if old not in source:
        raise RuntimeError('Ponto de normalização de CNPJ do processador local não encontrado.')
    return source.replace(old, new, 1)


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
    """Preserva URLs históricas dos scripts enquanto injeta a compatibilidade alfanumérica."""
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
        "script-src 'self' https://cdn.tailwindcss.com https://code.jquery.com https://cdn.datatables.net https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
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
        "script-src 'self' https://cdn.tailwindcss.com https://code.jquery.com https://cdn.datatables.net https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com"
    )
    if response.is_json or response.mimetype in {'text/html', 'application/json', 'application/javascript', 'text/css'}:
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/')
def index():
    html, _ = _separar_estilo_dashboard(render_template('dashboard.html'))
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
        '<script src="/static/browser_local_v2.js?v=2&cnpj=1"></script>'
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
        'cnpj_support': 'alphanumeric-14-rfb-v1',
        'csp_migration': 'strict-script-policy-report-only',
        'csp_enforcement': 'strict-script-policy-enforced-v6',
        'xml_upload': False,
    })
