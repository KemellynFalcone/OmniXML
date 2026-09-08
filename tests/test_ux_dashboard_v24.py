from pathlib import Path

import web_app_browser


def _template():
    return Path('templates/dashboard.html').read_text(encoding='utf-8')


def test_dashboard_v24_preserva_banner_e_kpis_reais():
    html = _template()
    assert 'id="card-boas-vindas"' in html
    assert 'Bem-vindo ao OmniXML Fiscal' in html
    assert 'id="btnProcessarDash"' in html
    assert 'Importar e Auditar XMLs' in html
    assert 'id="dash-nfe-ent-qtd"' in html
    assert 'id="dash-nfe-sai-qtd"' in html
    assert 'id="dash-nfce-qtd"' in html


def test_dashboard_v24_preview_fica_entre_kpis_e_graficos_reais():
    html = _template()
    preview = html.index('id="dashboard-preview-v24"')
    real = html.index('id="dashboard-real-v24"')
    grafico = html.index('id="graficoEvolucao"')
    sped = html.index('id="tab-sped"')
    assert preview < real < grafico < sped
    assert 'Previsão de impacto e próximos passos' in html
    assert 'Dados ilustrativos' in html


def test_dashboard_v24_graficos_reais_iniciam_ocultos_e_aparecem_apos_auditoria():
    html = _template()
    assert 'id="dashboard-real-v24" class="hidden"' in html
    assert "document.getElementById('dashboard-preview-v24')?.classList.add('hidden');" in html
    assert "document.getElementById('dashboard-real-v24')?.classList.remove('hidden');" in html
    assert html.index("dashboard-preview-v24')?.classList.add") > html.index("card-boas-vindas').classList.add")


def test_dashboard_v24_preview_nao_cria_style_attribute_e_csp_permanece_estrita():
    html = _template()
    start = html.index('id="dashboard-preview-v24"')
    end = html.index('id="dashboard-real-v24"', start)
    assert 'style=' not in html[start:end]
    response = web_app_browser.app.test_client().get('/')
    assert response.status_code == 200
    assert "style-src-attr 'none'" in response.headers['Content-Security-Policy']


def test_dashboard_v24_preserva_processamento_browser_local_e_graficos_existentes():
    html = _template()
    assert 'atualizarPainelDinamico(dados);' in html
    assert 'renderizarGraficos(dados.cfop, dados.cst, dados.diario);' in html
    assert 'id="graficoEvolucao"' in html
    assert 'id="graficoCFOP"' in html
    assert 'id="graficoCST"' in html
    health = web_app_browser.app.test_client().get('/health').get_json()
    assert health['processing'] == 'browser-local'
    assert health['xml_upload'] is False
