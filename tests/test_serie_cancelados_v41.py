from pathlib import Path


def test_cancelamentos_nfce_sao_agrupados_por_serie():
    js = Path('static/serie_cancelados_v41.js').read_text(encoding='utf-8')
    assert "tipo.includes('NFC-e')" in js
    assert "const serie = String(row?.serie" in js
    assert 'item.quantidade += 1' in js
    assert 'item.valor += Number(row?.valor || 0)' in js
    assert 'Cupons NFC-e cancelados' in js
    assert 'Cupons cancelados' in js
    assert 'Valor cancelado' in js


def test_resumo_usa_dados_ja_processados_dos_datatables():
    js = Path('static/serie_cancelados_v41.js').read_text(encoding='utf-8')
    assert "getTable('#tabelaCancelados')" in js
    assert "getTable('#tabelaSerie')" in js
    assert "draw.dt.omnixmlSerieCancelados" in js
    assert 'window.OmniXMLSerieCanceladosV41' in js


def test_loader_carrega_js_e_css_da_apuracao_por_serie():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'loadSerieCanceladosV41' in bridge
    assert '/static/serie_cancelados_v41.js?v=1' in bridge
    assert '/static/serie_cancelados_v41.css?v=1' in bridge
    assert 'loadSerieCanceladosV41();' in bridge


def test_modulo_nao_usa_estilo_inline_incompativel_com_csp():
    js = Path('static/serie_cancelados_v41.js').read_text(encoding='utf-8')
    assert '.style.' not in js
    assert 'style=' not in js
