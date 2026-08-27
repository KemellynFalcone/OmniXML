from flask import Flask, Response, jsonify, render_template

app = Flask(__name__, template_folder='templates', static_folder='static')


@app.get('/')
def index():
    html = render_template('dashboard.html')
    ponte = '<script src="/static/browser_local.js?v=1"></script>'
    return Response(html.replace('</body>', f'{ponte}</body>'), mimetype='text/html')


@app.get('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'OmniXML Web',
        'processing': 'browser-local',
        'xml_upload': False,
    })
