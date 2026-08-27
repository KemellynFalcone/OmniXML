import web_app_browser


def test_home_usa_processamento_local(monkeypatch, tmp_path):
    base = tmp_path / 'omnixml-web'
    base.mkdir()
    monkeypatch.setattr(web_app_browser.legacy, 'BASE_TEMP', base)
    client = web_app_browser.app.test_client()
    resposta = client.get('/')
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert 'Dashboard Geral' in html
    assert '/static/browser_local.js?v=1' in html


def test_health_permanece_disponivel(monkeypatch, tmp_path):
    base = tmp_path / 'omnixml-web'
    base.mkdir()
    monkeypatch.setattr(web_app_browser.legacy, 'BASE_TEMP', base)
    client = web_app_browser.app.test_client()
    resposta = client.get('/health')
    assert resposta.status_code == 200
