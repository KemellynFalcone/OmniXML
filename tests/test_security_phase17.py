import web_app_browser


def test_home_padrao_aplica_style_attr_estrito_apos_validacao_do_probe():
    response = web_app_browser.app.test_client().get('/')
    csp = response.headers['Content-Security-Policy']
    assert "style-src-attr 'none'" in csp
    assert "style-src-attr 'unsafe-inline'" not in csp
    assert 'X-OmniXML-Style-Attr-Probe' not in response.headers


def test_query_historica_do_probe_nao_altera_mais_a_politica():
    normal = web_app_browser.app.test_client().get('/')
    antigo_probe = web_app_browser.app.test_client().get('/?style_attr_strict=1')
    assert normal.headers['Content-Security-Policy'] == antigo_probe.headers['Content-Security-Policy']
    assert 'X-OmniXML-Style-Attr-Probe' not in antigo_probe.headers


def test_health_e_outros_recursos_tambem_recebem_politica_estrita():
    response = web_app_browser.app.test_client().get('/health?style_attr_strict=1')
    assert "style-src-attr 'none'" in response.headers['Content-Security-Policy']
    assert 'X-OmniXML-Style-Attr-Probe' not in response.headers


def test_health_registra_probe_validado_e_aposentado():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_attr_probe'] in {'opt-in-strict-query-v17', 'validated-and-retired-v18'}
    assert payload['style_attr_app'] == 'class-driven-progress-v13'
    assert payload['style_csp_enforcement'] in {'strict-elements-compat-attrs-v12', 'strict-elements-and-attrs-v18'}
