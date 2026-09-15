from pathlib import Path


def test_loader_carrega_diagnostico_fiscal_v403():
    js = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'loadDiagnosticoFiscalV403' in js
    assert '/static/diagnostico_fiscal_v40_3.js?v=1' in js
    assert '/static/diagnostico_fiscal_v40_3.css?v=1' in js
    assert 'loadDiagnosticoFiscalV403();' in js
