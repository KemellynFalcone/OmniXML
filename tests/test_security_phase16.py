from pathlib import Path


def test_inventario_v16_agrega_propriedades_por_origem():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'properties: emptyCounters()' in js
    assert 'recordStyleProperties' in js
    assert 'style.item(index)' in js
    assert 'styleAttrInventory.properties[bucket]' in js


def test_inventario_v16_agrega_elementos_e_snapshot_ordenado():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'elements: emptyCounters()' in js
    assert 'elementSignature' in js
    assert 'styleAttrSnapshot' in js
    assert 'sortedCounter' in js
    assert 'styleAttrInventory.snapshot = styleAttrSnapshot' in js


def test_inventario_v16_permite_reset_sem_remover_styles_do_dom():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'resetStyleAttrInventory' in js
    assert 'styleAttrInventory.reset = resetStyleAttrInventory' in js
    assert "removeAttribute('style')" not in js


def test_phase15_auto_width_continua_ativa():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert 'dataTable.defaults.autoWidth = false' in js
    assert 'configureDataTablesStyleBudget();' in js
