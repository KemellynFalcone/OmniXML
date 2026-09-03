import web_app_browser


def test_browser_local_nao_usa_style_inline_no_progresso():
    js = web_app_browser.app.test_client().get('/static/browser_local_v2.js').get_data(as_text=True)
    assert "c.style.display='block'" not in js
    assert 'b.style.width=' not in js
    assert "c.style.display='none'" not in js
    assert "classList.add('progress-visible')" in js
    assert "progress-pct-${p}" in js


def test_css_externo_publica_classes_de_progresso():
    css = web_app_browser.app.test_client().get('/static/dashboard_style_v9.css').get_data(as_text=True)
    assert '.progress-container.progress-visible { display: block; }' in css
    assert '.progress-bar.progress-pct-0 { width: 0%; }' in css
    assert '.progress-bar.progress-pct-50 { width: 50%; }' in css
    assert '.progress-bar.progress-pct-100 { width: 100%; }' in css


def test_home_cache_busta_browser_local_v13_sem_quebrar_url_historica():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    assert '/static/browser_local_v2.js?v=2&cnpj=1&style=13' in html
    assert '/static/browser_local_v2.js?v=2&cnpj=1' in html


def test_csp_mantem_vendor_compat_enquanto_report_only_testa_none():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert "style-src-attr 'unsafe-inline'" in enforced
    assert "style-src-attr 'none'" in report_only


def test_health_publica_phase13_e_preserva_phase12():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['style_attr_app'] == 'class-driven-progress-v13'
    assert payload['style_csp_enforcement'] == 'strict-elements-compat-attrs-v12'
    assert payload['tailwind_assets'] == 'compiled-local-css-v11'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
