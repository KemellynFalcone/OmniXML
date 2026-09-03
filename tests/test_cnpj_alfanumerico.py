from pathlib import Path

import web_app_browser


def test_home_carrega_suporte_cnpj_antes_do_processador_local():
    html = web_app_browser.app.test_client().get('/').get_data(as_text=True)
    suporte = html.index('/static/cnpj_alfanumerico_v1.js?v=1')
    local = html.index('/static/browser_local_v2.js?v=2')
    inutil = html.index('/static/inutilization_capture.js?v=1')
    assert suporte < local
    assert suporte < inutil


def test_utilitario_aceita_12_posicoes_alfanumericas_e_dv_numerico():
    js = Path('static/cnpj_alfanumerico_v1.js').read_text(encoding='utf-8')
    assert '/^[0-9A-Z]{12}[0-9]{2}$/' in js
    assert "replace(/[^0-9A-Z]/g, '')" in js
    assert 'charCodeAt(0) - 48' in js
    assert '[5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]' in js
    assert '[6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]' in js


def test_exemplo_oficial_primeiro_cnpj_tem_dv_12_pelo_algoritmo_rfb():
    base = '00000000E08G'

    def valor(char):
        return ord(char) - 48

    def digito(texto, pesos):
        resto = sum(valor(c) * p for c, p in zip(texto, pesos)) % 11
        return 0 if resto < 2 else 11 - resto

    dv1 = digito(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    dv2 = digito(base + str(dv1), [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    assert f'{dv1}{dv2}' == '12'


def test_processador_local_normaliza_cnpj_sem_converter_para_numero():
    js = web_app_browser.app.test_client().get('/static/browser_local_v2.js?v=2&cnpj=1').get_data(as_text=True)
    assert 'window.__omnixmlCnpj?.normalizar(cnpj)' in js
    assert "String(cnpj).trim().toUpperCase()" in js
    assert "Number(cnpj)" not in js
    assert "parseInt(cnpj" not in js


def test_inutilizacao_normaliza_cnpj_na_mesma_chave_textual():
    js = web_app_browser.app.test_client().get('/static/inutilization_capture.js?v=1&cnpj=1').get_data(as_text=True)
    assert "window.__omnixmlCnpj?.normalizar(valor('CNPJ'))" in js


def test_health_publica_suporte_alfanumerico_sem_apagar_contratos_anteriores():
    payload = web_app_browser.app.test_client().get('/health').get_json()
    assert payload['cnpj_support'] == 'alphanumeric-14-rfb-v1'
    assert payload['classification'] == 'cnpj-participants'
    assert payload['style_csp'] == 'own-css-external-strict-report-only-v9'
    assert payload['safe_renderers'] == 'escaped-dynamic-markup-and-data-sefaz-v8'
