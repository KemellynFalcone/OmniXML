import web_app_browser


def _directive(csp, name):
    prefix = f'{name} '
    for directive in csp.split(';'):
        directive = directive.strip()
        if directive.startswith(prefix):
            return directive
    return ''


def test_csp_aplicada_bloqueia_inline_em_elementos_de_estilo():
    response = web_app_browser.app.test_client().get('/')
    csp = response.headers['Content-Security-Policy']
    style = _directive(csp, 'style-src')
    elem = _directive(csp, 'style-src-elem')
    attr = _directive(csp, 'style-src-attr')

    assert "'unsafe-inline'" not in style
    assert "'unsafe-inline'" not in elem
    assert "'self'" in elem
    assert attr == "style-src-attr 'none'"


def test_report_only_experimenta_bloqueio_total_de_style_attr():
    response = web_app_browser.app.test_client().get('/')
    csp = response.headers['Content-Security-Policy-Report-Only']
    assert _directive(csp, 'style-src-attr') == "style-src-attr 'none'"
    assert "'unsafe-inline'" not in _directive(csp, 'style-src-elem')


def test_html_entregue_nao_contem_bloco_style_inline():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True).lower()
    assert '<style' not in html
    assert '/static/dashboard_style_v9.css?v=1' in html
    assert '/static/tailwind_v11.css?v=1' in html


def test_health_publica_phase12_e_preserva_fases_anteriores():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_csp_enforcement'] in {'strict-elements-compat-attrs-v12', 'strict-elements-and-attrs-v18'}
    assert payload['tailwind_assets'] == 'compiled-local-css-v11'
    assert payload['external_assets'] == 'local-datatables-i18n-pinned-chartjs-v10'
    assert payload['style_csp'] == 'own-css-external-strict-report-only-v9'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
