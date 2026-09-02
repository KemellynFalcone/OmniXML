from pathlib import Path

import web_app_browser


ROOT = Path(__file__).resolve().parents[1]
SECURITY_V3 = ROOT / 'static' / 'browser_security_v3.js'


def test_security_v3_carregado_antes_do_processador_local():
    response = web_app_browser.app.test_client().get('/')
    html = response.get_data(as_text=True)
    assert '/static/browser_security_v3.js?v=1' in html
    assert html.index('/static/browser_security_v3.js?v=1') < html.index('/static/browser_local_v2.js?v=2')


def test_security_v3_bloqueia_principais_vetores_dom_xss():
    js = SECURITY_V3.read_text(encoding='utf-8')
    assert "'SCRIPT'" in js
    assert "'IFRAME'" in js
    assert "'OBJECT'" in js
    assert "'EMBED'" in js
    assert "name.startsWith('on')" in js
    assert "name === 'srcdoc'" in js
    assert "javascript:" in js
    assert "data:text/html" in js
    assert 'MutationObserver' in js


def test_security_v3_restringe_navegacao_sefaz():
    js = SECURITY_V3.read_text(encoding='utf-8')
    assert 'key.length !== 44' in js
    assert 'isAllowedExternalUrl' in js
    assert 'SAFE_SEFAZ_HOST_SUFFIXES' in js
    assert 'Destino externo não autorizado' in js


def test_csp_report_only_mapeia_remocao_de_unsafe_inline():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert "'unsafe-inline'" in enforced
    assert "script-src 'self' 'unsafe-inline'" not in report_only
