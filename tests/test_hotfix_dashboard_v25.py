from pathlib import Path


def test_dashboard_v25_sincroniza_dados_reais_com_faixa_de_auditoria():
    js = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'syncDashboardPreviewV25' in js
    assert "document.getElementById('faixa-resumo-auditoria')" in js
    assert "document.getElementById('dashboard-preview-v24')" in js
    assert "document.getElementById('dashboard-real-v24')" in js
    assert "const hasRealAudit = !summary.classList.contains('hidden')" in js
    assert "preview.classList.add('hidden')" in js
    assert "real.classList.toggle('hidden', !hasRealAudit)" in js


def test_dashboard_v25_observa_somente_classe_da_faixa_resumo():
    js = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'dashboardObserver.observe(auditSummary' in js
    assert "attributeFilter: ['class']" in js
    assert 'subtree: true' not in js[js.index('const dashboardObserver'):]


def test_dashboard_v25_preserva_csp_sem_style_inline():
    js = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert ".style." not in js
    assert "setAttribute('style'" not in js
