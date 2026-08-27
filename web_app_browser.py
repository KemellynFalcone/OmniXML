from flask import Response, render_template

import web_app as legacy

app = legacy.app


def index_browser_local():
    html = render_template('dashboard.html')
    ponte = '<script src="/static/browser_local.js?v=1"></script>'
    return Response(html.replace('</body>', f'{ponte}</body>'), mimetype='text/html')


app.view_functions['index'] = index_browser_local
