from pathlib import Path

import web_app_browser


def test_home_carrega_tabela_falhas_v2_antes_da_validacao():
    client = web_app_browser.app.test_client()
    html = client.get('/').get_data(as_text=True)
    detalhe = html.index('/static/failure_table_v2.js?v=2')
    validacao = html.index('/static/browser_validation.js?v=1')
    assert detalhe < validacao


def test_script_extrai_chave_numero_valor_e_reconstroi_tabela():
    script = Path('static/failure_table_v2.js').read_text(encoding='utf-8')
    assert 'infNFe' in script
    assert 'nNF' in script
    assert 'vNF' in script
    assert 'Chave de Acesso' in script
    assert 'Valor total envolvido' in script
    assert 'Motivo' in script
    assert 'dtErros.destroy' in script
