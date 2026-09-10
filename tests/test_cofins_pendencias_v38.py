from pathlib import Path


def test_v38_disponibiliza_estados_de_revisao():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    for status in ['Crítico', 'Revisar', 'Conciliado', 'Justificado']:
        assert status in js
    assert 'Fila de revisão fiscal' in js


def test_v38_exige_motivo_para_justificado():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert "status === 'Justificado' && !justificativa" in js
    assert 'informe o motivo da justificativa' in js


def test_v38_persiste_tratativa_e_data_da_revisao():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'localStorage.setItem' in js
    assert 'atualizado_em' in js
    assert 'new Date().toISOString()' in js
