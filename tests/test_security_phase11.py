from pathlib import Path

import web_app_browser


def test_home_usa_tailwind_compilado_local_e_remove_cdn():
    response = web_app_browser.app.test_client().get('/')
    html = response.get_data(as_text=True)
    assert '/static/tailwind_v11.css?v=1' in html
    assert 'https://cdn.tailwindcss.com' not in html


def test_css_tailwind_compilado_contem_utilitarios_criticos_do_dashboard():
    css = Path('static/tailwind_v11.css').read_text(encoding='utf-8')
    assert 'tailwindcss v3.4.17' in css
    assert '.w-\\[280px\\]' in css
    assert '.bg-slate-950' in css
    assert '.md\\:grid-cols-3' in css
    assert '.hover\\:bg-blue-50:hover' in css


def test_css_tailwind_local_e_servido_com_no_store():
    response = web_app_browser.app.test_client().get('/static/tailwind_v11.css')
    assert response.status_code == 200
    assert response.mimetype == 'text/css'
    assert response.headers['Cache-Control'] == 'no-store'


def test_csp_nao_permite_mais_script_do_tailwind_cdn():
    response = web_app_browser.app.test_client().get('/')
    enforced = response.headers['Content-Security-Policy']
    report_only = response.headers['Content-Security-Policy-Report-Only']
    assert 'cdn.tailwindcss.com' not in enforced
    assert 'cdn.tailwindcss.com' not in report_only
    assert "script-src 'self'" in enforced
    assert 'https://cdn.datatables.net' in enforced
    assert 'https://cdn.jsdelivr.net' in enforced
    assert 'https://code.jquery.com' not in enforced


def test_health_publica_phase11_sem_quebrar_contratos_anteriores():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['tailwind_assets'] == 'compiled-local-css-v11'
    assert payload['external_assets'] == 'local-datatables-i18n-pinned-chartjs-v10'
    assert payload['style_csp'] == 'own-css-external-strict-report-only-v9'
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'


def test_build_tailwind_fica_reprodutivel_no_repositorio():
    package = Path('package.json').read_text(encoding='utf-8')
    config = Path('tailwind.config.js').read_text(encoding='utf-8')
    assert '"tailwindcss": "3.4.17"' in package
    assert 'build:tailwind' in package
    assert "'./templates/**/*.html'" in config
    assert "'./static/**/*.js'" in config
