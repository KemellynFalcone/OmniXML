from pathlib import Path

import web_app_browser


def test_browser_security_v2_inventaria_style_attrs_por_origem():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'styleAttrInventory' in js
    assert "dataTables: 0" in js
    assert "chartjs: 0" in js
    assert "app: 0" in js
    assert "other: 0" in js
    assert "element.closest('.dataTables_wrapper')" in js
    assert "element.tagName === 'CANVAS'" in js


def test_inventario_observa_mutacoes_de_style_sem_remover_estilos():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'new MutationObserver' in js
    assert "attributeFilter: ['style']" in js
    assert 'recordStyleAttribute(mutation.target)' in js
    assert "removeAttribute('style')" not in js


def test_inventario_fica_disponivel_para_diagnostico_no_browser():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'window.__omnixmlStyleAttrInventory = styleAttrInventory' in js
    assert 'scanExistingStyleAttributes' in js
    assert 'classifyStyledElement' in js


def test_home_continua_carregando_browser_security_v2():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert '/static/browser_security_v2.js?v=1&phase=7' in html


def test_csp_phase12_permanece_conservadora_enquanto_inventario_e_coletado():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert "style-src-attr 'unsafe-inline'" in enforced
    assert "style-src-attr 'none'" in report_only


def test_contratos_phase13_e_cnpj_permanecem_inalterados():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_attr_app'] == 'class-driven-progress-v13'
    assert payload['style_csp_enforcement'] == 'strict-elements-compat-attrs-v12'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
