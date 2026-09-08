import re

import web_app_browser


def test_sped_v23_renderiza_estado_vazio_conservador():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'id="placeholder-sped" class="sped-empty-v23"' in html
    assert 'Antecipe a análise antes de importar o SPED' in html
    assert 'Aguardando importação' in html
    assert 'Prévia visual:' in html


def test_sped_v23_preserva_fluxo_e_ids_fiscais_existentes():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert 'onclick="confrontarSPED()"' in html
    assert 'Importar SPED (.txt)' in html
    assert 'id="resultado-sped" class="hidden space-y-6"' in html
    assert 'id="btnDivergencias"' in html
    assert 'id="tabelaDivergencias"' in html
    assert 'id="mod-xml-nfe-ent"' in html
    assert 'id="mod-sped-nfce-sai"' in html


def test_sped_v23_placeholder_e_irmao_do_resultado_nao_fica_no_header():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    header_start = html.index('Confronto: Sistema vs XMLs')
    placeholder_start = html.index('id="placeholder-sped"', header_start)
    result_start = html.index('id="resultado-sped"', placeholder_start)
    header_fragment = html[header_start:placeholder_start]
    assert header_fragment.count('<div') <= header_fragment.count('</div>') + 3
    assert placeholder_start < result_start


def test_sped_v23_css_e_externo_e_responsivo():
    response = web_app_browser.app.test_client().get('/static/dashboard_style_v9.css')
    css = response.get_data(as_text=True)
    assert '.sped-empty-v23__hero {' in css
    assert 'grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.75fr)' in css
    assert '@media (max-width: 1050px)' in css
    assert '@media (max-width: 760px)' in css
    assert response.headers['Cache-Control'] == 'no-store'


def test_sped_v23_nao_adiciona_style_attribute_e_csp_permanece_estrita():
    response = web_app_browser.app.test_client().get('/')
    html = response.get_data(as_text=True)
    start = html.index('id="placeholder-sped"')
    end = html.index('id="resultado-sped"', start)
    preview = html[start:end]
    assert not re.search(r'\sstyle\s*=', preview, re.IGNORECASE)
    assert "style-src-attr 'none'" in response.headers['Content-Security-Policy']
