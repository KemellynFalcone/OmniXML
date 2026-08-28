from pathlib import Path

import web_app_browser


def test_home_carrega_diagnostico_compacto_v2():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert '/static/closing_diagnosis_v2.js?v=2' in html
    assert '/static/closing_diagnosis.js?v=1' not in html


def test_diagnostico_v2_fica_recolhido_e_usa_intervalo_da_pasta():
    script = Path('static/closing_diagnosis_v2.js').read_text(encoding='utf-8')
    assert "id=\"omnixml-diag-conteudo\" class=\"hidden" in script
    assert 'Lacunas nas saídas' in script
    assert 'Inicial na pasta' in script
    assert 'Final na pasta' in script
    assert "operacao || '').trim() !== 'Saída'" in script
    assert 'primeiro e o último documento de SAÍDA' in script
