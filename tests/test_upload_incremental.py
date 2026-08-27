import io

import web_app_v3


def configurar_temp(monkeypatch, tmp_path):
    base = tmp_path / 'omnixml-web'
    base.mkdir()
    monkeypatch.setattr(web_app_v3.legacy, 'BASE_TEMP', base)
    monkeypatch.setitem(web_app_v3.app.view_functions, 'index', web_app_v3.index_v3)
    return web_app_v3.app.test_client()


def test_home_usa_bridge_v3(monkeypatch, tmp_path):
    client = configurar_temp(monkeypatch, tmp_path)
    resposta = client.get('/')
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert 'Dashboard Geral' in html
    assert '/static/web_bridge_v3.js?v=3' in html


def test_consulta_vazia_recebe_lotes_separados(monkeypatch, tmp_path):
    client = configurar_temp(monkeypatch, tmp_path)

    inicio = client.post('/api/v3/consultas')
    assert inicio.status_code == 200
    consulta_id = inicio.get_json()['consulta_id']

    lote1 = client.post(
        f'/api/v3/consultas/{consulta_id}/uploads',
        data={'arquivos': (io.BytesIO(b'<NFe>'), 'a.xml')},
        content_type='multipart/form-data',
    )
    assert lote1.status_code == 200
    assert lote1.get_json()['resumo']['total'] == 1

    proc1 = client.post(f'/api/consultas/{consulta_id}/processar?limite=100')
    assert proc1.status_code == 200
    assert proc1.get_json()['resumo']['processados'] == 1

    lote2 = client.post(
        f'/api/v3/consultas/{consulta_id}/uploads',
        data={'arquivos': (io.BytesIO(b'<NFe>'), 'b.xml')},
        content_type='multipart/form-data',
    )
    assert lote2.status_code == 200
    assert lote2.get_json()['resumo']['total'] == 2

    proc2 = client.post(f'/api/consultas/{consulta_id}/processar?limite=100')
    assert proc2.status_code == 200
    assert proc2.get_json()['resumo']['processados'] == 2

    fim = client.post(f'/api/v3/consultas/{consulta_id}/finalizar-upload')
    assert fim.status_code == 200
    assert fim.get_json()['resumo']['total'] == 2
