from pathlib import Path


def test_v35_modal_nao_dispara_rerender_que_fecha_detalhes():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert "document.getElementById('cofins-auditor-v35-modal')" in js
    assert "if (document.getElementById('cofins-auditor-v35-modal')) return;" in js


def test_v35_delegacao_de_click_e_modal_sao_preservados():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert "event.target.closest('[data-cofins-details]')" in js
    assert "openDetails(group)" in js
    assert "data.cofinsDetails" not in js
    assert "cofins-auditor-v35-modal" in js


def test_v35_hotfix_nao_altera_calculos_fiscais():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'effectiveRate' in js
    assert 'buildDiagnostic' in js
    assert "group.diff = group.xmlValue - group.efdValue" in js
