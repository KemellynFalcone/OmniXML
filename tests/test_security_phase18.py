import web_app_browser


def test_csp_global_bloqueia_style_attributes_inline():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    assert "style-src-attr 'none'" in enforced
    assert "style-src-attr 'unsafe-inline'" not in enforced


def test_query_probe_antigo_nao_altera_mais_a_politica():
    normal = web_app_browser.app.test_client().get('/')
    antigo_probe = web_app_browser.app.test_client().get('/?style_attr_strict=1')
    assert normal.headers['Content-Security-Policy'] == antigo_probe.headers['Content-Security-Policy']
    assert 'X-OmniXML-Style-Attr-Probe' not in antigo_probe.headers


def test_report_only_permanece_alinhada_com_enforcement():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert "style-src-attr 'none'" in enforced
    assert "style-src-attr 'none'" in report_only


def test_health_reflete_enforcement_global_v18():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_csp_enforcement'] == 'strict-elements-and-attrs-v18'
    assert payload['style_attr_probe'] == 'validated-and-retired-v18'
    assert payload['style_attr_app'] == 'class-driven-progress-v13'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
