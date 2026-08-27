import io
import time
import uuid
import zipfile
from pathlib import Path

from flask import Response, jsonify, render_template, request

import web_app as legacy


app = legacy.app

# Cada requisição é propositalmente pequena. Pastas grandes são divididas no navegador.
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
V3_MAX_REQUEST_FILE_BYTES = 60 * 1024 * 1024
V3_MAX_EXPANDED_BATCH_BYTES = 120 * 1024 * 1024


def _novo_xml_incremental(pasta: Path, nome_original: str, conteudo: bytes, arquivos: list) -> None:
    if len(arquivos) >= legacy.MAX_XMLS_PER_CONSULTA:
        raise ValueError(f'Limite de {legacy.MAX_XMLS_PER_CONSULTA} XMLs por consulta excedido.')
    if not conteudo:
        raise ValueError(f'{Path(nome_original).name}: arquivo vazio.')
    if len(conteudo) > legacy.MAX_XML_BYTES:
        raise ValueError(f'{Path(nome_original).name}: XML acima de 20 MB.')

    identificador = f'{uuid.uuid4().hex}.xml'
    (pasta / 'uploads' / identificador).write_bytes(conteudo)
    arquivos.append({
        'nome': Path(nome_original).name or 'documento.xml',
        'caminho_original': nome_original,
        'stored': identificador,
        'size': len(conteudo),
    })


def _adicionar_lote(pasta: Path, uploads, estado: dict) -> tuple[int, int, list[str]]:
    arquivos = estado.setdefault('arquivos', [])
    avisos = estado.setdefault('avisos_upload', [])
    adicionados = 0
    bytes_expandidos = 0
    avisos_lote = []

    for upload in uploads:
        nome = upload.filename or ''
        if not nome:
            continue
        conteudo = upload.read()
        if len(conteudo) > V3_MAX_REQUEST_FILE_BYTES:
            raise ValueError(f'{Path(nome).name}: arquivo acima de 60 MB; para grandes volumes prefira selecionar a pasta.')

        lower = nome.lower()
        if lower.endswith('.xml'):
            _novo_xml_incremental(pasta, nome, conteudo, arquivos)
            adicionados += 1
            bytes_expandidos += len(conteudo)
            continue

        if lower.endswith('.zip'):
            try:
                with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
                    for info in zf.infolist():
                        if info.is_dir() or not info.filename.lower().endswith('.xml'):
                            continue
                        if info.flag_bits & 0x1:
                            aviso = f'{info.filename}: XML criptografado ignorado.'
                            avisos.append(aviso)
                            avisos_lote.append(aviso)
                            continue
                        if info.file_size > legacy.MAX_XML_BYTES:
                            aviso = f'{info.filename}: XML acima de 20 MB ignorado.'
                            avisos.append(aviso)
                            avisos_lote.append(aviso)
                            continue
                        if bytes_expandidos + info.file_size > V3_MAX_EXPANDED_BATCH_BYTES:
                            raise ValueError('ZIP expande acima de 120 MB em um único lote. Extraia o ZIP e selecione a pasta.')
                        xml = zf.read(info)
                        _novo_xml_incremental(pasta, info.filename, xml, arquivos)
                        adicionados += 1
                        bytes_expandidos += len(xml)
            except zipfile.BadZipFile as exc:
                raise ValueError(f'{Path(nome).name}: ZIP inválido ou corrompido.') from exc
            continue

        aviso = f'{Path(nome).name}: formato ignorado; use XML ou ZIP.'
        avisos.append(aviso)
        avisos_lote.append(aviso)

    return adicionados, bytes_expandidos, avisos_lote


def index_v3():
    html = render_template('dashboard.html')
    ponte = '<script src="/static/web_bridge_v3.js?v=3"></script>'
    return Response(html.replace('</body>', f'{ponte}</body>'), mimetype='text/html')


# Substitui somente a view da home; todas as rotas fiscais existentes continuam registradas.
app.view_functions['index'] = index_v3


@app.post('/api/v3/consultas')
def criar_consulta_v3():
    consulta_id = str(uuid.uuid4())
    pasta = legacy.BASE_TEMP / consulta_id
    (pasta / 'uploads').mkdir(parents=True)
    agora = time.time()
    estado = {
        'id': consulta_id,
        'created_at': agora,
        'updated_at': agora,
        'arquivos': [],
        'next_index': 0,
        'resultados': [],
        'erros_leitura': [],
        'avisos_upload': [],
    }
    legacy._salvar_estado(pasta, estado)
    return jsonify({'status': 'sucesso', 'consulta_id': consulta_id, 'resumo': legacy._resumo(estado)})


@app.post('/api/v3/consultas/<consulta_id>/uploads')
def upload_lote_v3(consulta_id):
    try:
        pasta = legacy._consulta_dir(consulta_id)
        estado = legacy._carregar_estado(pasta)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 404

    uploads = request.files.getlist('arquivos')
    if not uploads or not any(item.filename for item in uploads):
        return jsonify({'status': 'erro', 'mensagem': 'Lote sem arquivos.'}), 400

    try:
        adicionados, bytes_expandidos, avisos = _adicionar_lote(pasta, uploads, estado)
    except ValueError as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 400

    legacy._salvar_estado(pasta, estado)
    return jsonify({
        'status': 'sucesso',
        'adicionados': adicionados,
        'bytes_expandidos': bytes_expandidos,
        'avisos': avisos,
        'resumo': legacy._resumo(estado),
    })


@app.post('/api/v3/consultas/<consulta_id>/finalizar-upload')
def finalizar_upload_v3(consulta_id):
    try:
        pasta = legacy._consulta_dir(consulta_id)
        estado = legacy._carregar_estado(pasta)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 404

    if not estado.get('arquivos'):
        return jsonify({'status': 'erro', 'mensagem': 'Nenhum XML utilizável foi enviado.'}), 400
    estado['upload_finalizado'] = True
    legacy._salvar_estado(pasta, estado)
    return jsonify({'status': 'sucesso', 'resumo': legacy._resumo(estado)})


@app.errorhandler(413)
def lote_muito_grande_v3(_):
    return jsonify({
        'status': 'erro',
        'mensagem': 'Um lote ultrapassou 64 MB. O OmniXML deve dividi-lo automaticamente; tente novamente após atualizar a página.',
    }), 413
