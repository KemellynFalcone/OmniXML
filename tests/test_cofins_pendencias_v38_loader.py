from pathlib import Path


def test_v38_e_carregada_pelo_bridge_principal():
    js = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'loadCofinsPendenciasV38' in js
    assert '/static/cofins_pendencias_v38.js?v=1' in js
    assert 'loadCofinsPendenciasV38();' in js
