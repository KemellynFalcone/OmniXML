from pathlib import Path


def test_v31_exclui_origem_varejo_do_confronto_pis_cofins():
    js = Path('static/pis_cofins_xml_v30.js').read_text(encoding='utf-8')
    assert 'window.__omnixmlRetailOrigin?.isRetail?.(note.chave)' in js
    assert 'notas_varejo_excluidas' in js
    assert 'receita_varejo_excluida' in js


def test_v31_mantem_notas_varejo_rastreaveis_sem_somar_tributos():
    js = Path('static/pis_cofins_xml_v30.js').read_text(encoding='utf-8')
    start = js.index('if (isRetailOrigin(note))')
    end = js.index('outputs += 1', start)
    block = js[start:end]
    assert 'retailExcluded += 1' in block
    assert 'retailRevenue += note.itens.reduce' in block
    assert 'continue;' in block


def test_v31_fallback_so_exclui_nfe_integralmente_5929_6929():
    js = Path('static/pis_cofins_xml_v30.js').read_text(encoding='utf-8')
    assert "note.modelo === '55'" in js
    assert "cfops.every(cfop => cfop === '5929' || cfop === '6929')" in js
