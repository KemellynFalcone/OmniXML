from pathlib import Path

import web_app_browser


def test_datatables_desativa_autowidth_antes_da_inicializacao():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'function configureDataTablesStyleBudget()' in js
    assert 'dataTable.defaults.autoWidth = false' in js
    assert 'configureDataTablesStyleBudget();' in js


def test_configuracao_datatables_e_exposta_para_diagnostico():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'configureDataTablesStyleBudget,' in js
    assert 'window.__omnixmlSecurityV2' in js


def test_inventario_phase14_permanece_ativo_para_comparacao_pos_deploy():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'window.__omnixmlStyleAttrInventory = styleAttrInventory' in js
    assert "element.closest('.dataTables_wrapper')" in js
    assert "element.tagName === 'CANVAS'" in js


def test_csp_promovida_para_style_attrs_estritos_apos_medicao_real():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert "style-src-attr 'none'" in enforced
    assert "style-src-attr 'none'" in report_only


def test_contratos_fiscais_e_phase13_permanecem_intactos():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_attr_app'] == 'class-driven-progress-v13'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
    assert payload['processing'] == 'browser-local'
    assert payload['xml_upload'] is False
