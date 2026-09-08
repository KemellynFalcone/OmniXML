from pathlib import Path

import web_app_browser


def test_home_carrega_chartjs_local_e_remove_jsdelivr():
    response = web_app_browser.app.test_client().get('/')
    html = response.get_data(as_text=True)
    assert '/static/vendor/chart-4.5.1.umd.min.js?v=21' in html
    assert 'https://cdn.jsdelivr.net/npm/chart.js' not in html


def test_chartjs_vendor_e_exatamente_451():
    chart = Path('static/vendor/chart-4.5.1.umd.min.js')
    assert chart.is_file()
    assert 'Chart.js v4.5.1' in chart.read_text(encoding='utf-8')[:400]


def test_chartjs_local_e_servido_com_no_store():
    response = web_app_browser.app.test_client().get('/static/vendor/chart-4.5.1.umd.min.js')
    assert response.status_code == 200
    assert response.mimetype == 'text/javascript'
    assert response.headers['Cache-Control'] == 'no-store'


def test_script_csp_remove_jsdelivr_e_preserva_datatables():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert "script-src 'self' https://cdn.datatables.net;" in enforced
    assert "script-src 'self' https://cdn.datatables.net;" in report_only
    assert 'https://cdn.jsdelivr.net' not in enforced
    assert 'https://cdn.jsdelivr.net' not in report_only


def test_health_publica_phase21_e_preserva_contratos_criticos():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['script_assets'] == 'local-jquery-jszip-chartjs-v21'
    assert payload['style_csp_enforcement'] == 'strict-elements-and-attrs-v18'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
    assert payload['processing'] == 'browser-local'
    assert payload['xml_upload'] is False
