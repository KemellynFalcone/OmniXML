from pathlib import Path

import web_app_browser


def test_security_v2_cobre_tabela_de_erros_e_expoe_clone_seguro():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    assert "typeof dtErros !== 'undefined'" in js
    assert 'cloneForDisplay' in js
    assert "'&': '&amp;'" in js
    assert "'<': '&lt;'" in js
    assert "'>': '&gt;'" in js
    assert "'\"': '&quot;'" in js
    assert 'patchDataTables' in js


def test_home_carrega_security_v2_com_cache_bust_v7():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert '/static/browser_security_v2.js?v=2' in html


def test_health_publica_hardening_de_sinks_v7_sem_apagar_fases_anteriores():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['runtime_sinks'] == 'all-primary-datatables-display-escaped-v7'
    assert payload['safe_dom'] == 'closing-diagnosis-and-failure-table-v4'
    assert payload['inline_handlers'] == 'external-allowlisted-bridge-v5'
    assert payload['dashboard_runtime'] == 'externalized-v6'


def test_payloads_adversariais_sao_cobertos_pela_rotina_de_escape():
    js = Path('static/browser_security_v2.js').read_text(encoding='utf-8')
    # Evidência estática de que os caracteres necessários para neutralizar tags,
    # atributos e entidades HTML passam pela mesma função usada na cópia de display.
    assert "replace(/[&<>\"']/g" in js
    assert "return typeof value === 'string' ? escapeHtml(value) : value;" in js
