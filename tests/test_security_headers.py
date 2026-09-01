import web_app_browser


def test_home_aplica_cabecalhos_de_seguranca():
    response = web_app_browser.app.test_client().get('/')
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['Referrer-Policy'] == 'no-referrer'
    assert response.headers['Cross-Origin-Opener-Policy'] == 'same-origin'
    assert response.headers['Cross-Origin-Resource-Policy'] == 'same-origin'
    assert response.headers['Cache-Control'] == 'no-store'

    csp = response.headers['Content-Security-Policy']
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp


def test_health_publica_hardening_v1():
    response = web_app_browser.app.test_client().get('/health')
    assert response.get_json()['security_headers'] == 'hardening-v1'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
