from pathlib import Path

import web_app_browser


def test_home_carrega_diagnostico_antes_do_processador_local():
    client = web_app_browser.app.test_client()
    html = client.get('/').get_data(as_text=True)
    diagnostico = html.index('/static/closing_diagnosis.js?v=1')
    processador = html.index('/static/browser_local_v2.js?v=2')
    assert diagnostico < processador


def test_diagnostico_contem_regras_de_fechamento_e_lacunas():
    script = Path('static/closing_diagnosis.js').read_text(encoding='utf-8')
    assert 'detectarLacunas' in script
    assert 'Diagnóstico do Fechamento' in script
    assert 'XMLs com falha' in script
    assert 'Lacunas numéricas' in script
    assert 'Duplicidades' in script
    assert 'Não classificadas' in script
    assert 'Alertas tributários' in script
    assert 'inutilização' in script


def test_health_informa_diagnostico_de_fechamento():
    client = web_app_browser.app.test_client()
    payload = client.get('/health').get_json()
    assert payload['closing_diagnosis'] == 'sequence-gaps-and-pendencies'
