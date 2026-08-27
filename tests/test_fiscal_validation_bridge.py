import web_app_browser


def test_home_carrega_validacao_fiscal_antes_do_parser_local():
    client = web_app_browser.app.test_client()
    resposta = client.get('/')
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    validacao = html.index('/static/browser_validation.js?v=1')
    parser = html.index('/static/browser_local_v2.js?v=2')
    assert validacao < parser


def test_health_expoe_validacao_fiscal():
    client = web_app_browser.app.test_client()
    payload = client.get('/health').get_json()
    assert payload['processing'] == 'browser-local'
    assert payload['fiscal_validation'] == 'authorization-structure'
    assert payload['xml_upload'] is False
