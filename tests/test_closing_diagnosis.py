from pathlib import Path

import web_app_browser


def test_home_carrega_conciliacao_antes_do_diagnostico_e_processador():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    captura = html.index('/static/inutilization_capture.js?v=1')
    diagnostico = html.index('/static/closing_diagnosis_v2.js?v=3')
    processador = html.index('/static/browser_local_v2.js?v=2')
    assert captura < diagnostico < processador


def test_diagnostico_concilia_lacunas_com_inutilizacoes_homologadas():
    script = Path('static/closing_diagnosis_v2.js').read_text(encoding='utf-8')
    assert 'detectarLacunas' in script
    assert "operacao || '').trim() !== 'Saída'" in script
    assert 'Inutilizadas' in script
    assert 'A conferir' in script
    assert 'homologada' in script
    assert 'cStat 102' in script
    assert 'Canceladas continuam ocupando a numeração' in script


def test_captura_reconhece_proc_inut_e_cstat_102():
    script = Path('static/inutilization_capture.js').read_text(encoding='utf-8')
    assert 'procInutNFe' in script
    assert 'retInutNFe' in script
    assert "cStat === '102'" in script
    assert 'nNFIni' in script
    assert 'nNFFin' in script
    assert '__omnixmlInutilizacoes' in script


def test_health_informa_conciliacao_de_inutilizacoes():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['closing_diagnosis'] == 'sequence-with-inutilization-reconciliation'
    assert payload['inutilization_reconciliation'] == 'homologated-cstat-102'
