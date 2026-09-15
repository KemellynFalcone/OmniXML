from pathlib import Path


def test_v38_disponibiliza_estados_de_revisao():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    for status in ['Crítico', 'Revisar', 'Conciliado', 'Justificado']:
        assert status in js
    assert 'pendência${pending === 1 ?' in js
    assert 'divergência${items.length === 1 ?' in js


def test_v38_exige_motivo_para_justificado():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert "status === 'Justificado' && !justificativa" in js
    assert 'informe o motivo da justificativa' in js


def test_v38_persiste_tratativa_e_data_da_revisao():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'localStorage.setItem' in js
    assert 'atualizado_em' in js
    assert 'new Date().toISOString()' in js


def test_v38_conta_divergencias_atuais_mesmo_sem_tratativa_salva():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'function auditItems()' in js
    assert 'window.__omnixmlCofinsAuditorV34?.groups' in js
    assert "saved?.status || defaultStatusFromDiagnosis" in js
    assert "const pending = (counts['Crítico'] || 0) + (counts['Revisar'] || 0);" in js
