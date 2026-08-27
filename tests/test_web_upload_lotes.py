import io

import web_app
import web_app_v2


def configurar_temp(monkeypatch, tmp_path):
    base = tmp_path / 'omnixml-web'
    base.mkdir()
    monkeypatch.setattr(web_app, 'BASE_TEMP', base)
    return web_app_v2.app.test_client()


def test_consulta_v2_recebe_varios_lotes(monkeypatch, tmp_path):
    client = configurar_temp(monkeypatch, tmp_path)

    inicio = client.post('/api/v2/consultas')
    assert inicio.status_code == 200
    consulta_id = inicio.get_json()['consulta_id']

    lote1 = client.post(
        f'/api/v2/consultas/{consulta_id}/arquivos',
        data={'arquivos': (io.BytesIO(b'<NFe>'), 'a.xml')},
        content_type='multipart/form-data',
    )
    assert lote1.status_code == 200
    assert lote1.get_json()['resumo']['total'] == 1

    lote2 = client.post(
        f'/api/v2/consultas/{consulta_id}/arquivos',
        data={'arquivos': (io.BytesIO(b'<NFe>'), 'b.xml')},
        content_type='multipart/form-data',
    )
    assert lote2.status_code == 200
    assert lote2.get_json()['resumo']['total'] == 2

    processamento = client.post(f'/api/consultas/{consulta_id}/processar?limite=100')
    assert processamento.status_code == 200
    assert processamento.get_json()['resumo']['processados'] == 2


def test_home_v2_injeta_bridge_com_progresso(monkeypatch, tmp_path):
    client = configurar_temp(monkeypatch, tmp_path)
    resposta = client.get('/')
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert '/static/web_bridge_v2.js' in html
