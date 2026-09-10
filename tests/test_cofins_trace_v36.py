from pathlib import Path


def test_v36_nao_lista_todos_os_registros_quando_nao_ha_pareamento_seguro():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'buildDivergenceEvidence' in js
    assert 'pareamento_seguro' in js
    assert 'Diferença agregada sem vínculo individual conclusivo' in js


def test_v36_filtra_registros_conciliados_quando_ha_chave_nos_dois_lados():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'divergentXmlRows' in js
    assert 'divergentEfdRows' in js
    assert 'conciliadosOcultos' in js
    assert 'closeMoney(xmlValue - efdValue)' in js


def test_v36_preserva_detalhe_sob_demanda_e_hotfixes():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert "button.textContent = 'Ver detalhes'" in js
    assert "document.getElementById('cofins-auditor-v35-modal')" in js
    assert "document.addEventListener('click'" in js
