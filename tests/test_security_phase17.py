import web_app_browser


def test_home_padrao_preserva_compatibilidade_de_style_attr():
    response = web_app_browser.app.test_client().get('/')
    csp = response.headers['Content-Security-Policy']
    assert "style-src-attr 'unsafe-inline'" in csp
    assert 'X-OmniXML-Style-Attr-Probe' not in response.headers


def test_probe_opt_in_aplica_style_attr_none_apenas_na_home():
    response = web_app_browser.app.test_client().get('/?style_attr_strict=1')
    csp = response.headers['Content-Security-Policy']
    assert "style-src-attr 'none'" in csp
    assert "style-src-attr 'unsafe-inline'" not in csp
    assert response.headers['X-OmniXML-Style-Attr-Probe'] == 'strict-v17'


def test_probe_nao_altera_health_ou_outros_recursos():
    response = web_app_browser.app.test_client().get('/health?style_attr_strict=1')
    assert "style-src-attr 'unsafe-inline'" in response.headers['Content-Security-Policy']
    assert 'X-OmniXML-Style-Attr-Probe' not in response.headers


def test_health_expoe_capacidade_de_probe_v17():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_attr_probe'] == 'opt-in-strict-query-v17'
    assert payload['style_attr_app'] == 'class-driven-progress-v13'
    assert payload['style_csp_enforcement'] == 'strict-elements-compat-attrs-v12'
