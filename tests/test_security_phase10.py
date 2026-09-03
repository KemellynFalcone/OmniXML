import json
from pathlib import Path

import web_app_browser


def test_home_fixa_versao_do_chartjs():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js' in html
    assert '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>' not in html


def test_runtime_usa_idioma_local_do_datatables():
    runtime = web_app_browser.app.test_client().get('/static/dashboard_runtime_v6.js').get_data(as_text=True)
    assert '/static/datatables_ptbr_v10.json' in runtime
    assert 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json' not in runtime


def test_traducao_local_e_json_valido():
    path = Path(web_app_browser.app.root_path, 'static', 'datatables_ptbr_v10.json')
    payload = json.loads(path.read_text(encoding='utf-8'))
    assert payload['search'] == 'Pesquisar:'
    assert payload['paginate']['next'] == 'Próximo'
    assert payload['paginate']['previous'] == 'Anterior'


def test_static_traducao_pode_ser_servida_pela_aplicacao():
    response = web_app_browser.app.test_client().get('/static/datatables_ptbr_v10.json')
    assert response.status_code == 200
    assert response.get_json()['processing'] == 'Processando...'


def test_health_publica_phase10_e_preserva_cnpj_e_phase9():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['external_assets'] == 'local-datatables-i18n-pinned-chartjs-v10'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
    assert payload['style_csp'] == 'own-css-external-strict-report-only-v9'
    assert payload['safe_renderers'] == 'escaped-dynamic-markup-and-data-sefaz-v8'


def test_connect_src_continua_restrito_ao_proprio_servico():
    response = web_app_browser.app.test_client().get('/')
    csp = response.headers['Content-Security-Policy']
    assert "connect-src 'self'" in csp
