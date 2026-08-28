from pathlib import Path

import web_app_browser


def test_home_carrega_diagnostico_antes_do_processador_local():
    client = web_app_browser.app.test_client()
    html = client.get('/').get_data(as_text=True)
    diagnostico = html.index('/static/closing_diagnosis_v2.js?v=2')
    processador = html.index('/static/browser_local_v2.js?v=2')
    assert diagnostico < processador


def test_diagnostico_contem_regra_de_lacunas_somente_em_saidas():
    script = Path('static/closing_diagnosis_v2.js').read_text(encoding='utf-8')
    assert 'detectarLacunas' in script
    assert 'Diagnóstico do fechamento' in script
    assert 'Falhas fiscais' in script
    assert 'Lacunas nas saídas' in script
    assert 'Duplicidades' in script
    assert 'Alertas tributários' in script
    assert "operacao || '').trim() !== 'Saída'" in script
    assert 'Inicial na pasta' in script
    assert 'Final na pasta' in script
    assert 'Documentos de entrada não participam' in script


def test_health_informa_diagnostico_de_fechamento():
    client = web_app_browser.app.test_client()
    payload = client.get('/health').get_json()
    assert payload['closing_diagnosis'] == 'compact-conservative-v2'
