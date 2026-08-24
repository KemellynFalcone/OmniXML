from flask import Flask, jsonify, render_template, request
from defusedxml import ElementTree as ET

from core.validacao_documental import validar_documento


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024


@app.get('/')
def index():
    return render_template('web.html')


@app.get('/health')
def health():
    return jsonify({"status": "ok", "service": "OmniXML Web"})


@app.post('/api/validar-xml')
def validar_xml():
    arquivo = request.files.get('arquivo')
    if arquivo is None or not arquivo.filename:
        return jsonify({"status": "erro", "mensagem": "Selecione um arquivo XML."}), 400

    if not arquivo.filename.lower().endswith('.xml'):
        return jsonify({"status": "erro", "mensagem": "Envie um arquivo com extensão .xml."}), 400

    conteudo = arquivo.read()
    if not conteudo:
        return jsonify({"status": "erro", "mensagem": "O arquivo está vazio."}), 400

    try:
        root = ET.fromstring(conteudo)
    except ET.ParseError as exc:
        return jsonify({
            "status": "erro",
            "mensagem": "XML malformado ou corrompido.",
            "detalhe": str(exc),
        }), 422

    resultado = validar_documento(root, arquivo.filename)
    return jsonify({"status": "sucesso", "resultado": resultado})


@app.errorhandler(413)
def arquivo_muito_grande(_):
    return jsonify({
        "status": "erro",
        "mensagem": "Arquivo acima do limite de 10 MB da demonstração web.",
    }), 413
