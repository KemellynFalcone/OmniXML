from pathlib import Path

import web_app_browser


def test_sped_estado_vazio_vira_preview_orientado_a_acao():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'id="placeholder-sped" class="sped-preview-v22"' in html
    assert 'Veja o que será analisado antes de importar' in html
    assert 'Prévia visual — dados ilustrativos.' in html
    assert 'Aguardando importação' in html
    assert 'Arquivo SPED não importado' not in html


def test_sped_cta_importacao_e_principal_sem_mudar_acao():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'onclick="confrontarSPED()"' in html
    assert 'Importar SPED (.txt)' in html
    assert 'bg-blue-600 hover:bg-blue-700 text-white font-bold' in html


def test_sped_preview_preserva_resultado_e_divergencias_existentes():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'id="resultado-sped" class="hidden space-y-6"' in html
    assert 'id="btnDivergencias"' in html
    assert 'id="tabelaDivergencias"' in html
    assert 'id="mod-xml-nfe-ent"' in html
    assert 'id="mod-sped-nfce-sai"' in html


def test_sped_preview_nao_usa_style_attribute_e_csp_permanece_estrita():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    start = html.index('id="placeholder-sped"')
    end = html.index('id="resultado-sped"', start)
    preview = html[start:end]
    assert 'style=' not in preview
    response = web_app_browser.app.test_client().get('/')
    assert "style-src-attr 'none'" in response.headers['Content-Security-Policy']


def test_css_sped_v22_e_servido_no_stylesheet_externo():
    response = web_app_browser.app.test_client().get('/static/dashboard_style_v9.css')
    css = response.get_data(as_text=True)
    assert '.sped-preview-v22 {' in css
    assert '.sped-donut {' in css
    assert '@media (max-width: 900px)' in css
    assert response.headers['Cache-Control'] == 'no-store'


def test_health_publica_ux_sped_v22_sem_mudar_processamento():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['sped_empty_state'] == 'preview-action-guidance-v22'
    assert payload['processing'] == 'browser-local'
    assert payload['xml_upload'] is False
    assert payload['script_assets'] == 'local-jquery-jszip-chartjs-v21'
