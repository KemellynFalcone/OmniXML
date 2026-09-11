from pathlib import Path


def test_v401_carrega_modulo_de_arredondamento():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'loadBlocoMArredondamentoV401' in bridge
    assert '/static/bloco_m_arredondamento_v40_1.js?v=1' in bridge
    assert 'omnixmlBlocoMArredondamentoV401' in bridge


def test_v401_exige_consistencia_do_bloco_m():
    js = Path('static/bloco_m_arredondamento_v40_1.js').read_text(encoding='utf-8')
    assert 'blockMMatchesConsolidatedCalculation' in js
    assert 'base_ajustada' in js
    assert 'aliquota' in js
    assert 'contribuicao_periodo' in js
    assert 'hasApurationAdjustments' in js


def test_v401_usa_tolerancia_por_quantidade_de_itens():
    js = Path('static/bloco_m_arredondamento_v40_1.js').read_text(encoding='utf-8')
    assert 'documentaryItemCount' in js
    assert 'roundingTolerance' in js
    assert '* 0.005 + 0.005' in js


def test_v401_explica_arredondamento_sem_ocultar_diferenca():
    js = Path('static/bloco_m_arredondamento_v40_1.js').read_text(encoding='utf-8')
    assert 'Provável diferença de arredondamento' in js
    assert 'C170/C175 soma valores calculados por item' in js
    assert 'Bloco M calcula a contribuição sobre a base consolidada' in js
    assert 'Validar antes de tratar como divergência fiscal' in js


def test_v401_mantem_fallback_para_investigacao():
    js = Path('static/bloco_m_arredondamento_v40_1.js').read_text(encoding='utf-8')
    assert "kind: 'investigar'" in js
    assert 'Revisar outros blocos, ajustes e composição da apuração' in js


def test_v401_nao_altera_efd_automaticamente():
    js = Path('static/bloco_m_arredondamento_v40_1.js').read_text(encoding='utf-8')
    forbidden = ['alterarSped', 'salvarSped', 'corrigirAutomaticamente', 'aplicarAjusteFiscal']
    assert all(term not in js for term in forbidden)
