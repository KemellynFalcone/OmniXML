from pathlib import Path


def test_v37_expoe_conclusao_acao_e_confianca():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'buildActionGuidance' in js
    assert "['Diagnóstico', group.cause]" in js
    assert "['Impacto', money(Math.abs(group.diff))]" in js
    assert "['Evidência', guidance.evidenceText]" in js
    assert "['Ação sugerida', guidance.action]" in js
    assert "['Confiança', guidance.confidence]" in js


def test_v37_confiança_distingue_pareamento_de_agregado():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert "? 'Alta' : 'Média'" in js
    assert 'pareamento_seguro' in js
    assert 'sem vínculo individual conclusivo' in js


def test_v37_nao_aplica_ajuste_fiscal_automatico():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'validar antes de qualquer ajuste fiscal' in js
    assert 'acao_sugerida' in js
    assert 'confianca' in js
