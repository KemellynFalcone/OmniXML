import time
import uuid
from flask import Response, jsonify, render_template, request

import web_app as legacy

app = legacy.app


def index_v2():
    html = render_template('dashboard.html')
    ponte = '<script src="/static/web_bridge_v2.js?v=2"></script>'
    return Response(html.replace('</body>', f'{ponte}</body>'), mimetype='text/html')


# Substitui somente a view da home, preservando as demais rotas do backend atual.
app.view_functions['index'] = index_v2


@app.post('/api/v2/consultas')
def criar_consulta_vazia():
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
    return jsonify({
        'status': 'sucesso',
        'consulta_id': consulta_id,
        'resumo': legacy._resumo(estado),
    })


@app.post('/api/v2/consultas/<consulta_id>/arquivos')
def adicionar_arquivos_consulta(consulta_id):
    try:
        pasta = legacy._consulta_dir(consulta_id)
        estado = legacy._carregar_estado(pasta)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 404

    uploads = request.files.getlist('arquivos')
    if not uploads or not any(a.filename for a in uploads):
        return jsonify({'status': 'erro', 'mensagem': 'Nenhum arquivo recebido neste lote.'}), 400

    arquivos = estado.get('arquivos', [])
    avisos = estado.get('avisos_upload', [])
    try:
        for upload in uploads:
            legacy._adicionar_upload(pasta, upload, arquivos, avisos)
    except ValueError as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 400

    estado['arquivos'] = arquivos
    estado['avisos_upload'] = avisos
    legacy._salvar_estado(pasta, estado)

    return jsonify({
        'status': 'sucesso',
        'resumo': legacy._resumo(estado),
        'avisos': avisos,
    })
