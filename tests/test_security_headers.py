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
    assert "frame-src 'none'" in csp
    assert "media-src 'none'" in csp
    assert "base-uri 'self'" in csp

    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert "script-src 'self'" in report_only
    assert "script-src 'self' 'unsafe-inline'" not in report_only


def test_health_publica_hardening_phase3():
    response = web_app_browser.app.test_client().get('/health')
    health = response.get_json()
    assert health['security_headers'] == 'hardening-v1-csp-phase3'
    assert health['browser_security'].endswith('-v3')
    assert health['csp_migration'] == 'strict-script-policy-report-only'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
