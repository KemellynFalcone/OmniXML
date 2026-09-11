from pathlib import Path


def test_sped_header_status_is_compact():
    text = Path('static/sped_local_v26.js').read_text(encoding='utf-8')
    assert 'SPED processado com sucesso · ${fileLabel}' in text
    assert 'documento(s) C100 suportado(s)' not in text
    assert 'tratada(s) como origem varejo' not in text


def test_failure_table_shows_series():
    text = Path('static/browser_failure_details.js').read_text(encoding='utf-8')
    assert '>Série<' in text
    assert "meta.serie || '—'" in text
    assert 'Chave de acesso' in text
    assert 'Valor (R$)' in text
    assert 'colspan="6"' in text
