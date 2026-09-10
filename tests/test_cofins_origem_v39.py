from pathlib import Path


def test_v39_carrega_modulo_de_origem():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'loadCofinsOrigemV39' in bridge
    assert '/static/cofins_origem_v39.js?v=1' in bridge
    assert 'omnixmlCofinsOrigemV39' in bridge


def test_v39_expoe_hierarquia_competencia_cst_cfop_documento():
    js = Path('static/cofins_origem_v39.js').read_text(encoding='utf-8')
    assert 'Competência → CST → CFOP → Documento' in js
    assert 'cofins-v39-competencia' in js
    assert 'aggregateDocuments' in js
    assert "modalFilter" in js


def test_v39_captura_data_do_xml_e_efd():
    js = Path('static/cofins_origem_v39.js').read_text(encoding='utf-8')
    assert "text(first(ide, 'dhEmi')) || text(first(ide, 'dEmi'))" in js
    assert "fields[11] || fields[10]" in js
    assert 'competencia: competence(date)' in js


def test_v39_preserva_distincao_entre_pareamento_e_agregado():
    js = Path('static/cofins_origem_v39.js').read_text(encoding='utf-8')
    assert 'Pareamento por chave disponível' in js
    assert 'Diferença agregada' in js
    assert 'Sem chave conclusiva' in js


def test_v39_nao_aplica_ajuste_fiscal():
    js = Path('static/cofins_origem_v39.js').read_text(encoding='utf-8')
    forbidden = ['alterarSped', 'salvarSped', 'corrigirAutomaticamente', 'aplicarAjusteFiscal']
    assert all(term not in js for term in forbidden)
