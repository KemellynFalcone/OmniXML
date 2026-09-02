from pathlib import Path

import web_app_browser

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def test_closing_diagnosis_does_not_render_dynamic_rows_with_innerhtml():
    script = read('static/closing_diagnosis_v2.js')
    assert 'body.innerHTML=grupos.map' not in script
    assert 'exp.innerHTML' not in script
    assert 'createElement' in script
    assert 'cell.textContent' in script


def test_failure_table_structure_is_built_with_dom_api():
    script = read('static/failure_table_v2.js')
    assert 'table.innerHTML = `' not in script
    assert 'summary.innerHTML = `' not in script
    assert 'createElement' in script


def test_health_reports_safe_dom_phase4():
    response = web_app_browser.app.test_client().get('/health')
    assert response.get_json()['browser_security'].endswith('safe-dom-v4')
