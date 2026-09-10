from pathlib import Path


def test_v34_calcula_base_aliquota_efetiva_e_diagnostico():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'effectiveRate' in js
    assert 'Base de cálculo divergente' in js
    assert 'Alíquota efetiva divergente' in js
    assert 'Base e alíquota efetiva divergem' in js


def test_v34_usa_detalhes_xml_e_efd_existentes():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'xml?.cofins_detalhes' in js
    assert 'window.__omnixmlEfdContribLast' in js
    assert 'row.base_cofins' in js
    assert 'row.valor_cofins' in js


def test_v34_preserva_rastreabilidade_e_nao_corrige_fiscal_automaticamente():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'row.chave' in js
    assert 'row.source' in js
    assert 'row.line' in js
    assert 'deve ser validada antes de qualquer ajuste fiscal' in js


def test_v34_assets_sao_locais_e_carregados_pelo_bridge():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert "'/static/cofins_auditor_v34.js?v=1'" in bridge
    assert "'/static/cofins_auditor_v34.css?v=1'" in bridge
    assert 'loadCofinsAuditorV34();' in bridge
