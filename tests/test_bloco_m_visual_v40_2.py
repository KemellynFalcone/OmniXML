from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'static' / 'bloco_m_visual_v40_2.js').read_text(encoding='utf-8')
CSS = (ROOT / 'static' / 'bloco_m_visual_v40_2.css').read_text(encoding='utf-8')
LOADER = (ROOT / 'static' / 'inline_handler_bridge_v5.js').read_text(encoding='utf-8')


def test_visual_layer_is_loaded():
    assert 'loadBlocoMVisualV402' in LOADER
    assert '/static/bloco_m_visual_v40_2.css?v=1' in LOADER
    assert '/static/bloco_m_visual_v40_2.js?v=1' in LOADER


def test_summary_cards_and_status_badges_exist():
    assert 'bloco-m-v40-2__summary' in JS
    assert 'Provável arredondamento' in JS
    assert 'Conciliado' in JS
    assert 'Revisar' in JS
    assert 'C170/C175' in JS
    assert "tax === 'PIS' ? 'M210' : 'M610'" in JS


def test_visual_observer_only_reacts_to_block_creation():
    assert "node.id === 'bloco-m-v40'" in JS
    assert "section.dataset.visualV402 === '1'" in JS


def test_css_has_card_table_and_reconciliation_layouts():
    for selector in [
        '.bloco-m-v40-2__tax-card',
        '.bloco-m-v40-2__status--rounding',
        '#bloco-m-v40 .bloco-m-v40__table-wrap',
        '#bloco-m-v40 .bloco-m-v40__reconciliation',
        '#bloco-m-v40 .bloco-m-v40__grid',
    ]:
        assert selector in CSS
