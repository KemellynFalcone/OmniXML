from pathlib import Path

import web_app_browser


def test_home_carrega_jquery_e_jszip_locais():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert '/static/vendor/jquery-3.7.0.min.js?v=20' in html
    assert '/static/vendor/jszip-3.10.1.min.js?v=20' in html
    assert 'https://cdn.jsdelivr.net/npm/jquery@3.7.0' not in html
    assert 'https://cdn.jsdelivr.net/npm/jszip@3.10.1' not in html
    assert 'https://code.jquery.com/jquery-3.7.0.min.js' not in html
    assert 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js' not in html


def test_vendor_assets_sao_exatamente_as_versoes_fixadas():
    jquery = Path('static/vendor/jquery-3.7.0.min.js')
    jszip = Path('static/vendor/jszip-3.10.1.min.js')
    assert jquery.is_file()
    assert jszip.is_file()
    assert 'jQuery v3.7.0' in jquery.read_text(encoding='utf-8')[:200]
    assert 'JSZip v3.10.1' in jszip.read_text(encoding='utf-8')[:300]


def test_vendor_assets_sao_servidos_com_no_store():
    client = web_app_browser.app.test_client()
    for path in ('/static/vendor/jquery-3.7.0.min.js', '/static/vendor/jszip-3.10.1.min.js'):
        response = client.get(path)
        assert response.status_code == 200
        assert response.mimetype == 'text/javascript'
        assert response.headers['Cache-Control'] == 'no-store'


def test_csp_mantem_apenas_hosts_externos_ainda_necessarios_para_scripts():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    expected = "script-src 'self' https://cdn.datatables.net https://cdn.jsdelivr.net"
    assert expected in enforced
    assert expected in report_only
    assert 'https://code.jquery.com' not in enforced


def test_health_publica_phase20_e_preserva_contratos_criticos():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['script_assets'] == 'local-jquery-jszip-pinned-chartjs-v20'
    assert payload['style_csp_enforcement'] == 'strict-elements-and-attrs-v18'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
    assert payload['processing'] == 'browser-local'
    assert payload['xml_upload'] is False
