import re

import web_app_browser


def _style_directive(csp):
    for directive in csp.split(';'):
        directive = directive.strip()
        if directive.startswith('style-src '):
            return directive
    return ''


def test_home_externaliza_css_proprio_do_dashboard():
    response = web_app_browser.app.test_client().get('/')
    html = response.get_data(as_text=True)
    assert '/static/dashboard_style_v9.css?v=1' in html
    assert re.findall(r'<style[^>]*>.*?</style>', html, flags=re.I | re.S) == []


def test_css_externo_preserva_estilos_principais():
    response = web_app_browser.app.test_client().get('/static/dashboard_style_v9.css')
    assert response.status_code == 200
    assert response.mimetype == 'text/css'
    css = response.get_data(as_text=True)
    assert ".kpi-card" in css
    assert ".tab-btn.active" in css
    assert ".progress-container" in css


def test_csp_aplicada_preserva_compatibilidade_e_report_only_testa_estilo_estrito():
    response = web_app_browser.app.test_client().get('/')
    enforced = _style_directive(response.headers['Content-Security-Policy'])
    report_only = _style_directive(response.headers['Content-Security-Policy-Report-Only'])
    assert "'unsafe-inline'" in enforced
    assert "'unsafe-inline'" not in report_only
    assert "'self'" in report_only


def test_dependencias_externas_que_bloqueiam_enforcement_total_estao_inventariadas():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'https://cdn.tailwindcss.com' in html
    assert 'https://cdn.datatables.net' in html


def test_health_publica_migracao_de_estilos_v9_sem_apagar_fases_anteriores():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_csp'] == 'own-css-external-strict-report-only-v9'
    assert payload['safe_renderers'] == 'escaped-dynamic-markup-and-data-sefaz-v8'
    assert payload['runtime_sinks'] == 'all-primary-datatables-display-escaped-v7'
    assert payload['dashboard_runtime'] == 'externalized-v6'
