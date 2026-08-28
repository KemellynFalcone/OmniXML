from pathlib import Path

import web_app_browser


def test_home_carrega_detalhes_financeiros_antes_da_validacao():
    client = web_app_browser.app.test_client()
    html = client.get('/').get_data(as_text=True)
    detalhe = html.index('/static/browser_failure_details.js?v=1')
    validacao = html.index('/static/browser_validation.js?v=1')
    assert detalhe < validacao


def test_script_extrai_chave_numero_valor_e_totaliza():
    script = Path('static/browser_failure_details.js').read_text(encoding='utf-8')
    assert "infNFe" in script
    assert "nNF" in script
    assert "vNF" in script
    assert "omnixml-falhas-valor" in script
    assert "omnixml-falhas-detalhes" in script
