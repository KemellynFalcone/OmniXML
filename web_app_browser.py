from flask import Flask, Response, jsonify, render_template

app = Flask(__name__, template_folder='templates', static_folder='static')


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
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://code.jquery.com https://cdn.datatables.net https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "worker-src 'self' blob:"
    )
    # Política futura mais estrita em modo somente-relatório. Ela permite medir o
    # débito de scripts inline sem quebrar o dashboard enquanto a migração é feita.
    response.headers['Content-Security-Policy-Report-Only'] = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "script-src 'self' https://cdn.tailwindcss.com https://code.jquery.com https://cdn.datatables.net https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com"
    )
    if response.is_json or response.mimetype in {'text/html', 'application/json'}:
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/')
def index():
    html = render_template('dashboard.html')
    ponte = (
        '<script src="/static/browser_security_v2.js?v=1"></script>'
        '<script src="/static/browser_security_v3.js?v=1"></script>'
        '<script src="/static/failure_table_v2.js?v=2"></script>'
        '<script src="/static/browser_validation.js?v=1"></script>'
        '<script src="/static/failure_summary.js?v=1"></script>'
        '<script src="/static/inutilization_capture.js?v=1"></script>'
        '<script src="/static/closing_diagnosis_v2.js?v=3"></script>'
        '<script src="/static/browser_local_v2.js?v=2"></script>'
        '<script src="/static/inline_handler_bridge_v5.js?v=1"></script>'
    )
    return Response(html.replace('</body>', f'{ponte}</body>'), mimetype='text/html')


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
        'csp_migration': 'strict-script-policy-report-only',
        'xml_upload': False,
    })
