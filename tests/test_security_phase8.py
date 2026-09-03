import web_app_browser


def _runtime():
    response = web_app_browser.app.test_client().get('/static/dashboard_runtime_v6.js')
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_runtime_v8_escapa_dados_dinamicos_dos_renderizadores():
    js = _runtime()
    assert 'const escapeRuntimeHtml' in js
    assert "escapeRuntimeHtml(data)" in js
    assert "escapeRuntimeHtml(d)" in js
    assert '${escapeRuntimeHtml(chaveFormatada)}' in js
    assert '⚠️ ${escapeRuntimeHtml(d)}' in js


def test_consulta_sefaz_nao_usa_onclick_dinamico_no_runtime_entregue():
    js = _runtime()
    assert 'data-omnixml-sefaz-chave' in js
    assert 'data-omnixml-sefaz-url' in js
    assert 'onclick="copiarEAbrir(' not in js


def test_bridge_v8_delega_consulta_sefaz_sem_eval():
    response = web_app_browser.app.test_client().get('/static/safe_renderers_v8.js')
    assert response.status_code == 200
    js = response.get_data(as_text=True)
    assert 'data-omnixml-sefaz-chave' in js
    assert 'window.copiarEAbrir(chave, url)' in js
    assert 'eval(' not in js
    assert 'new Function' not in js


def test_home_carrega_bridge_v8_e_runtime_com_cache_bust():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert '/static/dashboard_runtime_v6.js?v=1&phase=8' in html
    assert '/static/safe_renderers_v8.js?v=1' in html


def test_health_publica_phase8_sem_apagar_evidencias_anteriores():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['safe_renderers'] == 'escaped-dynamic-markup-and-data-sefaz-v8'
    assert payload['runtime_sinks'] == 'all-primary-datatables-display-escaped-v7'
    assert payload['csp_enforcement'] == 'strict-script-policy-enforced-v6'


def test_payload_xss_nao_permanece_como_markup_executavel_apos_escape():
    escape = web_app_browser._RUNTIME_ESCAPE_HELPER
    assert '&lt;' in escape
    assert '&gt;' in escape
    assert '&quot;' in escape
    assert '&#39;' in escape
