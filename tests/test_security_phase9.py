import re

import web_app_browser


def _style_directive(csp):
    for directive in csp.split(';'):
        directive = directive.strip()
        if directive.startswith('style-src '):
            return directive
    return ''


def _directive(csp, name):
    prefix = f'{name} '
    for directive in csp.split(';'):
        directive = directive.strip()
        if directive.startswith(prefix):
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
    enforced_csp = response.headers['Content-Security-Policy']
    report_csp = response.headers['Content-Security-Policy-Report-Only']
    enforced = _style_directive(enforced_csp)
    report_only = _style_directive(report_csp)

    assert "'self'" in enforced
    assert "'unsafe-inline'" not in report_only
    assert "'self'" in report_only

    # A Phase 9 mantinha unsafe-inline no style-src geral. Fases posteriores podem
    # estreitar a política e isolar compatibilidade apenas em style-src-attr.
    if "'unsafe-inline'" not in enforced:
        assert "'unsafe-inline'" in _directive(enforced_csp, 'style-src-attr')


def test_dependencias_externas_restantes_para_enforcement_total_estao_inventariadas():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'https://cdn.tailwindcss.com' not in html
    assert '/static/tailwind_v11.css?v=1' in html
    assert 'https://cdn.datatables.net' in html


def test_health_publica_migracao_de_estilos_v9_sem_apagar_fases_anteriores():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_csp'] == 'own-css-external-strict-report-only-v9'
    assert payload['safe_renderers'] == 'escaped-dynamic-markup-and-data-sefaz-v8'
    assert payload['runtime_sinks'] == 'all-primary-datatables-display-escaped-v7'
    assert payload['dashboard_runtime'] == 'externalized-v6'
