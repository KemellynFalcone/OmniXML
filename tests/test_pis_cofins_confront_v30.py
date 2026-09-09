from pathlib import Path


def test_v30_captura_pis_cofins_dos_xmls_localmente():
    js = Path('static/pis_cofins_xml_v30.js').read_text(encoding='utf-8')
    assert "taxGroup(det, 'PIS')" in js
    assert "taxGroup(det, 'COFINS')" in js
    assert "emitente_cnpj" in js
    assert "cancelled.has(note.chave)" in js
    assert "window.__omnixmlXmlPisCofins" in js


def test_v30_confronta_documentos_com_c170_c175():
    js = Path('static/sped_contrib_local_v29.js').read_text(encoding='utf-8')
    assert 'renderConfront(summary' in js
    assert 'window.__omnixmlXmlPisCofins?.snapshot?.()' in js
    assert "'Receita documental'" in js
    assert "'PIS documental'" in js
    assert "'COFINS documental'" in js
    assert 'M200/M210 e M600/M610' in js


def test_v30_remove_previews_sem_dados_operacionais():
    css = Path('static/ux_cleanup_v30.css').read_text(encoding='utf-8')
    assert '#dashboard-preview-v24' in css
    assert '.sped-empty-v23__preview' in css
    assert 'display: none !important' in css


def test_v30_carrega_assets_locais_e_preserva_contratos_anteriores():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert "'/static/pis_cofins_xml_v30.js?v=1'" in bridge
    assert "'/static/ux_cleanup_v30.css?v=1'" in bridge
    assert "script.src = '/static/sped_local_v26.js?v=1'" in bridge
    assert "script.src = '/static/sped_contrib_local_v29.js?v=1'" in bridge
    app = Path('web_app_browser.py').read_text(encoding='utf-8')
    assert "style-src-attr 'none'" in app
