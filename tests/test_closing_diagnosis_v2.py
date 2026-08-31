from pathlib import Path

import web_app_browser


def test_home_carrega_diagnostico_v3():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert '/static/closing_diagnosis_v2.js?v=3' in html
    assert '/static/inutilization_capture.js?v=1' in html
    assert '/static/closing_diagnosis.js?v=1' not in html


def test_diagnostico_fica_recolhido_e_separa_justificado_de_pendente():
    script = Path('static/closing_diagnosis_v2.js').read_text(encoding='utf-8')
    assert 'id="omnixml-diag-conteudo" class="hidden' in script
    assert 'Inutilizadas' in script
    assert 'A conferir' in script
    assert 'inutilizadas' in script
    assert 'conferir' in script
    assert "operacao || '').trim() !== 'Saída'" in script
