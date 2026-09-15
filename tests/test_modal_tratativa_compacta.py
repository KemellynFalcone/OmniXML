from pathlib import Path


def test_tratativa_fica_recolhida_por_padrao():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'Registrar tratativa' in js
    assert 'id="cofins-v38-form" hidden' in js
    assert "toggle.setAttribute('aria-expanded', open ? 'true' : 'false')" in js
    assert "setOpen(false);" in js


def test_remove_confianca_duplicada_do_diagnostico():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'function removeDuplicateConfidence(modal)' in js
    assert "textContent?.trim() === 'Confiança'" in js
    assert 'confidenceRow?.remove();' in js


def test_tratativa_mantem_status_justificativa_e_persistencia():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert "const STATUS = ['Crítico', 'Revisar', 'Conciliado', 'Justificado'];" in js
    assert 'cofins-v38-justificativa' in js
    assert 'localStorage.setItem' in js
    assert 'new Date().toISOString()' in js
