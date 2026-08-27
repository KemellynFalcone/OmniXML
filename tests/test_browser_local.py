import web_app_browser


def test_home_usa_processamento_local():
    client = web_app_browser.app.test_client()
    resposta = client.get('/')
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert 'Dashboard Geral' in html
    assert '/static/browser_local.js?v=1' in html


def test_health_indica_processamento_local():
    client = web_app_browser.app.test_client()
    resposta = client.get('/health')
    assert resposta.status_code == 200
    payload = resposta.get_json()
    assert payload['processing'] == 'browser-local'
    assert payload['xml_upload'] is False
