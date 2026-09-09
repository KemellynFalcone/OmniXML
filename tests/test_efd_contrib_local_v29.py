from pathlib import Path


def test_v29_processa_c170_e_c175_localmente():
    js = Path('static/sped_contrib_local_v29.js').read_text(encoding='utf-8')
    assert "reg === 'C170'" in js
    assert "reg === 'C175'" in js
    assert "currentC100Oper !== '1'" in js
    assert "const cstPis = String(fields[25]" in js
    assert "const cstPis = String(fields[5]" in js


def test_v29_mapeia_campos_fiscais_esperados():
    js = Path('static/sped_contrib_local_v29.js').read_text(encoding='utf-8')
    assert 'receita: Math.max(0, gross - discount)' in js
    assert 'base_pis: brNumber(fields[26])' in js
    assert 'valor_pis: brNumber(fields[30])' in js
    assert 'receita: brNumber(fields[3])' in js
    assert 'valor_pis: brNumber(fields[10])' in js
    assert 'valor_cofins: brNumber(fields[16])' in js


def test_v29_preenche_tabela_existente_sem_upload():
    js = Path('static/sped_contrib_local_v29.js').read_text(encoding='utf-8')
    assert "window.importarPisCofins = () => input.click()" in js
    assert "document.getElementById('total-receita-pis')" in js
    assert 'window.dtPisCofins.clear().rows.add(summary.csts).draw()' in js
    assert "document.getElementById('res-pis-cofins')" in js
    assert "fetch('/importar_sped_contribuicoes')" not in js


def test_v29_carregado_pelo_bridge_e_csp_preservada():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'loadEfdContribLocalV29' in bridge
    assert "script.src = '/static/sped_contrib_local_v29.js?v=1'" in bridge
    app = Path('web_app_browser.py').read_text(encoding='utf-8')
    assert "style-src-attr 'none'" in app
