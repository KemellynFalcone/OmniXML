from pathlib import Path


def test_v28_identifica_cfop_varejo_por_chave():
    js = Path('static/retail_origin_v28.js').read_text(encoding='utf-8')
    assert "new Set(['5929', '6929'])" in js
    assert "text(first(ide, 'mod')) !== '55'" in js
    assert "byKey.set(chave" in js
    assert "listaCfops.every(cfop => RETAIL_CFOPS.has(cfop))" in js
    assert 'window.__omnixmlRetailOrigin' in js


def test_v28_exclui_nfe_varejo_apenas_da_saida_confrontada():
    js = Path('static/sped_local_v26.js').read_text(encoding='utf-8')
    assert 'xmlNfeOutputForConfront' in js
    assert 'window.__omnixmlRetailOrigin?.isRetail?.(nota?.chave)' in js
    assert "String(nota?.operacao || '') !== 'Saída'" in js
    assert "String(nota?.status || '').includes('Cancelado')" in js
    assert "'mod-xml-nfe-sai': xmlNfeSai.total" in js
    assert 'const difSai = Number(xmlNfeSai.total || 0) - summary.sped_nfe_sai' in js


def test_v28_mantem_rastreabilidade_da_exclusao_varejo():
    js = Path('static/sped_local_v26.js').read_text(encoding='utf-8')
    assert 'nfe_saida_varejo_excluida: xmlNfeSai.varejo' in js
    assert 'qtd_nfe_varejo_excluida: xmlNfeSai.quantidadeVarejo' in js
    assert 'NF-e 5.929/6.929 tratada(s) como origem varejo' in js


def test_v28_carregado_localmente_sem_relaxar_csp():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert "'/static/retail_origin_v28.js?v=1'" in bridge
    assert 'loadRetailOriginV28' in bridge
    app = Path('web_app_browser.py').read_text(encoding='utf-8')
    assert "style-src-attr 'none'" in app
