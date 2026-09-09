from pathlib import Path


def test_v27_reconcilia_falha_sem_protocolo_com_inutilizacao_homologada():
    js = Path('static/failure_reconciliation_v27.js').read_text(encoding='utf-8')
    assert 'Blob.prototype.text' in js
    assert 'window.__omnixmlInutilizacoes' in js
    assert "if (!item?.homologada) return false" in js
    assert "String(item.modelo || '') !== String(meta.modelo || '')" in js
    assert 'normalizeInt(item.serie) !== meta.serie' in js
    assert 'meta.numero >= ini && meta.numero <= fim' in js
    assert 'sem protocolo|nfeProc|protNFe' in js


def test_v27_preserva_erros_nao_justificados():
    js = Path('static/failure_reconciliation_v27.js').read_text(encoding='utf-8')
    assert 'if (!failureCanBeJustified(row)) return true' in js
    assert 'if (!inut) return true' in js
    assert 'dados.erros = result.erros' in js
    assert 'dados.total_erros = result.erros.length' in js
    assert 'syncErrorTable(result.erros)' in js


def test_v27_reconciliacao_exige_mesma_empresa_emitente():
    js = Path('static/failure_reconciliation_v27.js').read_text(encoding='utf-8')
    assert 'issuer !== company' in js
    assert 'inutCnpj !== company' in js
    assert 'issuer !== inutCnpj' in js


def test_v27_tabela_erros_fica_contida_e_quebra_texto():
    css = Path('static/failure_reconciliation_v27.css').read_text(encoding='utf-8')
    assert '#tabelaErros_wrapper' in css
    assert 'max-width: 100%' in css
    assert 'table-layout: fixed' in css
    assert 'overflow-wrap: anywhere' in css
    assert 'white-space: normal !important' in css


def test_v27_carregado_pelo_bridge_sem_inline_script():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert '/static/failure_reconciliation_v27.js?v=1' in bridge
    assert 'loadFailureReconciliationV27()' in bridge
