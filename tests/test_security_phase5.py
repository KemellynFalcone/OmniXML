from pathlib import Path

import web_app_browser

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / 'static' / 'inline_handler_bridge_v5.js'


def test_inline_handler_bridge_is_loaded_after_browser_processor():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    bridge = '/static/inline_handler_bridge_v5.js?v=1'
    processor = '/static/browser_local_v2.js?v=2'
    assert bridge in html
    assert html.index(processor) < html.index(bridge)


def test_bridge_uses_allowlist_and_does_not_eval_inline_code():
    script = BRIDGE.read_text(encoding='utf-8')
    assert 'const ALLOWED = new Set' in script
    assert "'mudarAba'" in script
    assert "'iniciarProcessamento'" in script
    assert "'confrontarSPED'" in script
    assert "element.removeAttribute('onclick')" in script
    assert "element.addEventListener('click'" in script
    assert 'eval(' not in script
    assert 'new Function' not in script


def test_bridge_rejects_arbitrary_javascript_arguments():
    script = BRIDGE.read_text(encoding='utf-8')
    assert "token === 'this'" in script
    assert "token === 'null'" in script
    assert 'parseArg' in script
    assert 'if (!parsed.ok) return null' in script


def test_health_reports_inline_handler_migration_v5():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['inline_handlers'] == 'external-allowlisted-bridge-v5'
