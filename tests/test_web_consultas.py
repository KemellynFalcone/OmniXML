import io
import zipfile

import web_app


def configurar_temp(monkeypatch, tmp_path):
    base = tmp_path / 'omnixml-web'
    base.mkdir()
    monkeypatch.setattr(web_app, 'BASE_TEMP', base)
    return web_app.app.test_client()


def test_consulta_processa_xml_malformado_e_pode_ser_excluida(monkeypatch, tmp_path):
    client = configurar_temp(monkeypatch, tmp_path)

    resposta = client.post(
        '/api/consultas',
        data={'arquivos': (io.BytesIO(b'<NFe>'), 'ruim.xml')},
        content_type='multipart/form-data',
    )
    assert resposta.status_code == 200
    consulta = resposta.get_json()
    consulta_id = consulta['consulta_id']
    assert consulta['resumo']['total'] == 1

    processamento = client.post(f'/api/consultas/{consulta_id}/processar')
    assert processamento.status_code == 200
    assert processamento.get_json()['concluido'] is True

    resultado = client.get(f'/api/consultas/{consulta_id}').get_json()
    assert resultado['resumo']['processados'] == 1
    assert resultado['resumo']['erros'] == 1
    assert resultado['erros_leitura'][0]['codigo'] == 'XML-001'

    exclusao = client.delete(f'/api/consultas/{consulta_id}')
    assert exclusao.status_code == 200
    assert client.get(f'/api/consultas/{consulta_id}').status_code == 404


def test_zip_importa_apenas_xmls(monkeypatch, tmp_path):
    client = configurar_temp(monkeypatch, tmp_path)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.writestr('pasta/a.xml', '<NFe>')
        zf.writestr('b.xml', '<NFe>')
        zf.writestr('ignorar.txt', 'nao fiscal')
    buffer.seek(0)

    resposta = client.post(
        '/api/consultas',
        data={'arquivos': (buffer, 'lote.zip')},
        content_type='multipart/form-data',
    )
    assert resposta.status_code == 200
    payload = resposta.get_json()
    assert payload['resumo']['total'] == 2


def test_relatorio_csv_e_gerado_sob_demanda(monkeypatch, tmp_path):
    client = configurar_temp(monkeypatch, tmp_path)
    resposta = client.post(
        '/api/consultas',
        data={'arquivos': (io.BytesIO(b'<NFe>'), 'ruim.xml')},
        content_type='multipart/form-data',
    )
    consulta_id = resposta.get_json()['consulta_id']
    client.post(f'/api/consultas/{consulta_id}/processar')

    csv_resp = client.get(f'/api/consultas/{consulta_id}/relatorio.csv')
    assert csv_resp.status_code == 200
    assert csv_resp.mimetype == 'text/csv'
    assert 'ruim.xml' in csv_resp.get_data(as_text=True)
