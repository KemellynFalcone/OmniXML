from pathlib import Path


def test_v33_oculta_tabela_legada_pis_cofins_e_wrapper_datatables():
    css = Path('static/ux_cleanup_v30.css').read_text(encoding='utf-8')
    assert '#tabelaPisCofins_wrapper' in css
    assert '#tabelaPisCofins' in css
    assert 'display: none !important' in css


def test_v33_preserva_confronto_e_diagnostico_novos():
    js = Path('static/sped_contrib_local_v29.js').read_text(encoding='utf-8')
    assert 'Confronto documental: XMLs × EFD-Contribuições' in js
    assert 'Diagnóstico da diferença de COFINS' in js
    assert 'buildCofinsDiagnostic' in js
