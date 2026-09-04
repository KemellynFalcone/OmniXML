import web_app_browser


def test_home_consolida_jquery_e_jszip_no_jsdelivr():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'https://cdn.jsdelivr.net/npm/jquery@3.7.0/dist/jquery.min.js' in html
    assert 'https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js' in html
    assert 'https://code.jquery.com/jquery-3.7.0.min.js' not in html
    assert 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js' not in html


def test_chartjs_e_datatables_permanecem_versionados():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js' in html
    assert 'https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js' in html
    assert 'https://cdn.datatables.net/buttons/2.4.1/js/dataTables.buttons.min.js' in html


def test_script_src_remove_host_jquery_historico():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert 'https://code.jquery.com' not in enforced
    assert 'https://code.jquery.com' not in report_only
    assert 'https://cdn.jsdelivr.net' in enforced
    assert 'https://cdn.datatables.net' in enforced
    assert "style-src-attr 'none'" in enforced


def test_health_publica_phase19_sem_apagar_contratos_anteriores():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['script_assets'] == 'jquery-jszip-jsdelivr-pinned-v19'
    assert payload['style_csp_enforcement'] == 'strict-elements-and-attrs-v18'
    assert payload['processing'] == 'browser-local'
    assert payload['xml_upload'] is False
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
