from pathlib import Path


def test_v34_observer_nao_retroalimenta_renderizacao():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'observer.disconnect();' in js
    assert 'observer.observe(document.body, observerOptions);' in js
    assert 'let refreshing = false;' in js
    assert 'render();\n    observer.observe(document.body, observerOptions);' in js


def test_v34_observer_reconecta_mesmo_se_render_falhar():
    js = Path('static/cofins_auditor_v34.js').read_text(encoding='utf-8')
    assert 'try {' in js
    assert 'finally {' in js
    assert 'refreshing = false;' in js
