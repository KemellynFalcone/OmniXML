from pathlib import Path


def test_failure_table_exibe_serie_e_exporta_coluna():
    js = Path('static/failure_table_v2.js').read_text(encoding='utf-8')

    assert "['Arquivo', 'Nº Cupom/Nota', 'Série', 'Chave de Acesso', 'Valor (R$)', 'Motivo']" in js
    assert "serie: txt(first(ide, 'serie')) || '—'" in js
    assert 'function seriesFor(row)' in js
    assert "const serieChave = chave.slice(22, 25)" in js
    assert "table.dataset.failureV2 = '1'" in js
    assert "buttons: [{ extend: 'excelHtml5'" in js
