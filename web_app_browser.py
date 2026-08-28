from flask import Flask, Response, jsonify, render_template

app = Flask(__name__, template_folder='templates', static_folder='static')


@app.get('/')
def index():
    html = render_template('dashboard.html')
    ponte = (
        '<script src="/static/browser_failure_details.js?v=1"></script>'
        '<script src="/static/browser_validation.js?v=1"></script>'
        '<script src="/static/failure_summary.js?v=1"></script>'
        '<script src="/static/browser_local_v2.js?v=2"></script>'
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
        'failure_financial_details': True,
        'xml_upload': False,
    })
