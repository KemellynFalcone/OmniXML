from pathlib import Path

import web_app_browser


ROOT = Path(__file__).resolve().parents[1]


def test_browser_security_script_is_loaded_before_local_processor():
    response = web_app_browser.app.test_client().get('/')
    html = response.get_data(as_text=True)

    security = html.index('/static/browser_security_v2.js?v=1')
    validation = html.index('/static/browser_validation.js?v=1')
    processor = html.index('/static/browser_local_v2.js?v=2')

    assert security < validation < processor


def test_browser_security_has_file_and_memory_limits():
    script = (ROOT / 'static' / 'browser_security_v2.js').read_text(encoding='utf-8')

    assert 'maxFiles: 50000' in script
    assert 'maxFileBytes: 20 * 1024 * 1024' in script
    assert 'maxTotalBytes: 1536 * 1024 * 1024' in script
    assert "event.stopImmediatePropagation()" in script


def test_browser_security_escapes_xml_derived_display_values():
    script = (ROOT / 'static' / 'browser_security_v2.js').read_text(encoding='utf-8')

    assert 'escapeHtml' in script
    assert 'cloneForDisplay' in script
    assert 'dtNFe' in script
    assert 'dtNFCe' in script
    assert 'dtProdutos' in script
    assert 'dtAuditoria' in script
    assert 'table.rows.add = function(rows)' in script


def test_health_reports_browser_security_v2():
    response = web_app_browser.app.test_client().get('/health')
    assert response.get_json()['browser_security'] == 'xss-display-escape-and-file-limits-v2'
