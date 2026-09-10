from pathlib import Path


def test_v40_carrega_modulo_bloco_m():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'loadBlocoMV40' in bridge
    assert '/static/bloco_m_v40.js?v=1' in bridge
    assert 'omnixmlBlocoMV40' in bridge


def test_v40_le_registros_principais_do_bloco_m():
    js = Path('static/bloco_m_v40.js').read_text(encoding='utf-8')
    for registro in ['M200', 'M210', 'M600', 'M610']:
        assert registro in js
    assert 'parseM210' in js
    assert 'parseM610' in js
    assert 'parseConsolidacao' in js


def test_v40_separa_documental_detalhamento_e_recolhimento():
    js = Path('static/bloco_m_v40.js').read_text(encoding='utf-8')
    assert 'C170/C175' in js
    assert 'M210/M610' in js
    assert 'M200/M600' in js
    assert 'credito_periodo' in js
    assert 'retencao_nao_cumulativa' in js
    assert 'outras_deducoes_nao_cumulativa' in js
    assert 'total_recolher' in js


def test_v40_nao_classifica_toda_diferenca_como_erro():
    js = Path('static/bloco_m_v40.js').read_text(encoding='utf-8')
    assert 'não é automaticamente um erro' in js
    assert 'outros blocos' in js
    assert 'ajustes' in js


def test_v40_nao_altera_efd_automaticamente():
    js = Path('static/bloco_m_v40.js').read_text(encoding='utf-8')
    forbidden = ['alterarSped', 'salvarSped', 'corrigirAutomaticamente', 'aplicarAjusteFiscal']
    assert all(term not in js for term in forbidden)
