from pathlib import Path


def test_v32_xml_expoe_detalhes_cofins_por_documento():
    js = Path('static/pis_cofins_xml_v30.js').read_text(encoding='utf-8')
    assert 'cofinsDetails = []' in js
    assert 'cst_cofins: item.cst_cofins' in js
    assert 'valor_cofins: item.valor_cofins' in js
    assert 'cofins_detalhes: cofinsDetails' in js
    assert 'version: 32' in js


def test_v32_efd_preserva_chave_numero_e_linha_para_rastreabilidade():
    js = Path('static/sped_contrib_local_v29.js').read_text(encoding='utf-8')
    assert "chave: String(fields[9]" in js
    assert "numero: String(fields[8]" in js
    assert 'line: lineNumber' in js
    assert 'source,' in js


def test_v32_diagnostica_cofins_por_cst_e_cfop():
    js = Path('static/sped_contrib_local_v29.js').read_text(encoding='utf-8')
    assert 'buildCofinsDiagnostic' in js
    assert "const key = `${cst || '00'}|${cfop || 'N/A'}`" in js
    assert 'group.xml += Number(row.valor_cofins' in js
    assert 'group.efd += Number(row.valor_cofins' in js
    assert "['CST COFINS', 'CFOP', 'COFINS XML', 'COFINS EFD', 'Diferença', 'Rastreabilidade']" in js


def test_v32_remove_tabela_legada_sem_relaxar_csp():
    js = Path('static/sped_contrib_local_v29.js').read_text(encoding='utf-8')
    assert 'hideLegacyPisTable' in js
    assert "closest?.('.dataTables_wrapper')" in js
    assert "wrapper.classList.add('hidden')" in js
    assert '.style.' not in js
    app = Path('web_app_browser.py').read_text(encoding='utf-8')
    assert "style-src-attr 'none'" in app
