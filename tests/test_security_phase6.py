import re

import web_app_browser


def _script_directive(csp):
    for directive in csp.split(';'):
        directive = directive.strip()
        if directive.startswith('script-src '):
            return directive
    return ''


def test_home_externaliza_runtime_principal():
    response = web_app_browser.app.test_client().get('/')
    html = response.get_data(as_text=True)
    assert '/static/dashboard_runtime_v6.js?v=1' in html
    inline_scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>.*?</script>', html, flags=re.I | re.S)
    assert inline_scripts == []


def test_runtime_externo_preserva_funcoes_do_dashboard():
    response = web_app_browser.app.test_client().get('/static/dashboard_runtime_v6.js')
    assert response.status_code == 200
    assert response.mimetype == 'application/javascript'
    js = response.get_data(as_text=True)
    assert 'function mudarAba(' in js
    assert 'function atualizarPainelDinamico(' in js
    assert 'function renderizarGraficos(' in js
    assert 'window.copiarEAbrir' in js


def test_csp_aplicada_remove_unsafe_inline_de_scripts():
    response = web_app_browser.app.test_client().get('/')
    csp = response.headers['Content-Security-Policy']
    script_src = _script_directive(csp)
    assert script_src.startswith("script-src 'self'")
    assert "'unsafe-inline'" not in script_src
    assert "style-src 'self' 'unsafe-inline'" in csp


def test_bridge_migra_consulta_sefaz_dinamica():
    from pathlib import Path
    js = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert "'copiarEAbrir'" in js
    assert 'element.removeAttribute(\'onclick\')' in js
    assert 'eval(' not in js
    assert 'new Function' not in js


def test_health_publica_runtime_e_csp_v6():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['dashboard_runtime'] == 'externalized-v6'
    assert payload['csp_migration'] == 'strict-script-policy-enforced-v6'
