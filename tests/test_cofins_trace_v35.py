from pathlib import Path


def test_v35_resume_rastreabilidade_na_tabela_principal():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'traceSummary' in js
    assert "XMLs ×" in js
    assert 'Ver detalhes' in js
    assert 'data-cofins-details' in js


def test_v35_abre_detalhes_sob_demanda_sem_inline_handler():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'openDetails' in js
    assert "document.addEventListener('click'" in js
    assert 'onclick=' not in js
    assert 'setAttribute(\'style\'' not in js


def test_v35_detalha_apenas_documentos_divergentes_quando_houver_pareamento():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'XMLs divergentes' in js
    assert 'Registros EFD divergentes' in js
    assert "['Nota','Chave','CFOP','CST','Base COFINS','COFINS','Referência']" in js
    assert "row.source || 'EFD'" in js
    assert 'row.line' in js


def test_v35_preserva_hotfix_antiloop_v34():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'observer.disconnect()' in js
    assert 'refreshing' in js
    assert 'observer.observe(document.body, observerOptions)' in js
