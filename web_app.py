import csv
import io
import json
import shutil
import tempfile
import time
import uuid
import zipfile
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request
from defusedxml import ElementTree as ET

from core.validacao_documental import validar_documento


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

BASE_TEMP = Path(tempfile.gettempdir()) / 'omnixml-web'
BASE_TEMP.mkdir(parents=True, exist_ok=True)
SESSION_TTL_SECONDS = 2 * 60 * 60
MAX_XML_BYTES = 20 * 1024 * 1024
MAX_TOTAL_XML_BYTES = 500 * 1024 * 1024
MAX_XMLS_PER_CONSULTA = 5000
BATCH_DEFAULT = 100


def _consulta_dir(consulta_id: str) -> Path:
    if not consulta_id or not all(c.isalnum() or c == '-' for c in consulta_id):
        raise ValueError('Consulta inválida.')
    pasta = BASE_TEMP / consulta_id
    if not pasta.exists() or not pasta.is_dir():
        raise FileNotFoundError('Consulta não encontrada ou já expirada.')
    return pasta


def _state_path(pasta: Path) -> Path:
    return pasta / 'state.json'


def _carregar_estado(pasta: Path) -> dict:
    return json.loads(_state_path(pasta).read_text(encoding='utf-8'))


def _salvar_estado(pasta: Path, estado: dict) -> None:
    estado['updated_at'] = time.time()
    tmp = pasta / 'state.tmp'
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(_state_path(pasta))


def _limpar_expiradas() -> None:
    agora = time.time()
    for pasta in BASE_TEMP.iterdir():
        if not pasta.is_dir():
            continue
        try:
            estado = _carregar_estado(pasta)
            referencia = estado.get('updated_at') or estado.get('created_at') or pasta.stat().st_mtime
            if agora - float(referencia) > SESSION_TTL_SECONDS:
                shutil.rmtree(pasta, ignore_errors=True)
        except Exception:
            try:
                if agora - pasta.stat().st_mtime > SESSION_TTL_SECONDS:
                    shutil.rmtree(pasta, ignore_errors=True)
            except OSError:
                pass


def _novo_xml(pasta: Path, nome_original: str, conteudo: bytes, arquivos: list) -> None:
    if len(arquivos) >= MAX_XMLS_PER_CONSULTA:
        raise ValueError(f'Limite de {MAX_XMLS_PER_CONSULTA} XMLs por consulta excedido.')
    if not conteudo:
        raise ValueError(f'{nome_original}: arquivo vazio.')
    if len(conteudo) > MAX_XML_BYTES:
        raise ValueError(f'{nome_original}: XML acima de 20 MB.')
    total_atual = sum(int(item.get('size', 0)) for item in arquivos)
    if total_atual + len(conteudo) > MAX_TOTAL_XML_BYTES:
        raise ValueError('Os XMLs expandidos excedem o limite temporário de 500 MB por consulta.')

    identificador = f'{uuid.uuid4().hex}.xml'
    (pasta / 'uploads' / identificador).write_bytes(conteudo)
    arquivos.append({'nome': Path(nome_original).name or 'documento.xml', 'stored': identificador, 'size': len(conteudo)})


def _adicionar_upload(pasta: Path, upload, arquivos: list, avisos: list) -> None:
    nome = Path(upload.filename or '').name
    if not nome:
        return

    lower = nome.lower()
    if lower.endswith('.xml'):
        _novo_xml(pasta, nome, upload.read(), arquivos)
        return

    if lower.endswith('.zip'):
        conteudo_zip = upload.read()
        try:
            with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zf:
                for info in zf.infolist():
                    if info.is_dir() or not info.filename.lower().endswith('.xml'):
                        continue
                    if info.flag_bits & 0x1:
                        avisos.append(f'{info.filename}: XML criptografado ignorado.')
                        continue
                    if info.file_size > MAX_XML_BYTES:
                        avisos.append(f'{info.filename}: XML acima de 20 MB ignorado.')
                        continue
                    try:
                        _novo_xml(pasta, Path(info.filename).name, zf.read(info), arquivos)
                    except ValueError as exc:
                        if '500 MB' in str(exc) or '5000' in str(exc):
                            raise
                        avisos.append(str(exc))
        except zipfile.BadZipFile:
            raise ValueError(f'{nome}: ZIP inválido ou corrompido.')
        return

    avisos.append(f'{nome}: formato ignorado; use XML ou ZIP.')


def _resumo(estado: dict) -> dict:
    resultados = estado.get('resultados', [])
    contagem = {'OK': 0, 'ALERTA': 0, 'ERRO': 0}
    for documento in resultados:
        severidades = {v.get('severidade') for v in documento.get('validacoes', [])}
        if 'ERRO' in severidades:
            contagem['ERRO'] += 1
        elif 'ALERTA' in severidades:
            contagem['ALERTA'] += 1
        else:
            contagem['OK'] += 1
    return {
        'total': len(estado.get('arquivos', [])),
        'processados': estado.get('next_index', 0),
        'pendentes': max(0, len(estado.get('arquivos', [])) - estado.get('next_index', 0)),
        'conformes': contagem['OK'],
        'alertas': contagem['ALERTA'],
        'erros': contagem['ERRO'] + len(estado.get('erros_leitura', [])),
    }


@app.before_request
def housekeeping():
    _limpar_expiradas()


@app.get('/')
def index():
    return render_template('web.html')


@app.get('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'OmniXML Web', 'storage': 'temporary'})


@app.post('/api/consultas')
def criar_consulta():
    uploads = request.files.getlist('arquivos')
    if not uploads or not any(a.filename for a in uploads):
        return jsonify({'status': 'erro', 'mensagem': 'Selecione XMLs ou um arquivo ZIP.'}), 400

    consulta_id = str(uuid.uuid4())
    pasta = BASE_TEMP / consulta_id
    (pasta / 'uploads').mkdir(parents=True)

    arquivos = []
    avisos = []
    try:
        for upload in uploads:
            _adicionar_upload(pasta, upload, arquivos, avisos)
    except ValueError as exc:
        shutil.rmtree(pasta, ignore_errors=True)
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 400

    if not arquivos:
        shutil.rmtree(pasta, ignore_errors=True)
        return jsonify({'status': 'erro', 'mensagem': 'Nenhum XML utilizável foi encontrado.', 'avisos': avisos}), 400

    agora = time.time()
    estado = {
        'id': consulta_id,
        'created_at': agora,
        'updated_at': agora,
        'arquivos': arquivos,
        'next_index': 0,
        'resultados': [],
        'erros_leitura': [],
        'avisos_upload': avisos,
    }
    _salvar_estado(pasta, estado)
    return jsonify({'status': 'sucesso', 'consulta_id': consulta_id, 'resumo': _resumo(estado), 'avisos': avisos})


@app.post('/api/consultas/<consulta_id>/processar')
def processar_consulta(consulta_id):
    try:
        pasta = _consulta_dir(consulta_id)
        estado = _carregar_estado(pasta)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 404

    try:
        limite = int(request.args.get('limite', BATCH_DEFAULT))
    except ValueError:
        limite = BATCH_DEFAULT
    limite = max(1, min(limite, 500))

    arquivos = estado['arquivos']
    inicio = estado.get('next_index', 0)
    fim = min(len(arquivos), inicio + limite)

    for item in arquivos[inicio:fim]:
        caminho = pasta / 'uploads' / item['stored']
        try:
            conteudo = caminho.read_bytes()
            root = ET.fromstring(conteudo)
            estado['resultados'].append(validar_documento(root, item['nome']))
        except ET.ParseError as exc:
            estado['erros_leitura'].append({
                'arquivo': item['nome'],
                'codigo': 'XML-001',
                'mensagem': 'XML malformado ou corrompido.',
                'detalhe': str(exc),
            })
        except Exception as exc:
            estado['erros_leitura'].append({
                'arquivo': item['nome'],
                'codigo': 'PROC-001',
                'mensagem': 'Falha inesperada durante a análise.',
                'detalhe': str(exc),
            })
        finally:
            caminho.unlink(missing_ok=True)

    estado['next_index'] = fim
    _salvar_estado(pasta, estado)
    concluido = fim >= len(arquivos)
    return jsonify({'status': 'sucesso', 'concluido': concluido, 'resumo': _resumo(estado)})


@app.get('/api/consultas/<consulta_id>')
def obter_consulta(consulta_id):
    try:
        pasta = _consulta_dir(consulta_id)
        estado = _carregar_estado(pasta)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 404

    return jsonify({
        'status': 'sucesso',
        'consulta_id': consulta_id,
        'resumo': _resumo(estado),
        'resultados': estado.get('resultados', []),
        'erros_leitura': estado.get('erros_leitura', []),
        'avisos': estado.get('avisos_upload', []),
    })


@app.get('/api/consultas/<consulta_id>/relatorio.csv')
def relatorio_csv(consulta_id):
    try:
        pasta = _consulta_dir(consulta_id)
        estado = _carregar_estado(pasta)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 404

    saida = io.StringIO()
    writer = csv.writer(saida, delimiter=';')
    writer.writerow(['Arquivo', 'Tipo', 'Numero', 'Serie', 'Data', 'Operacao', 'Valor', 'Status', 'Chave'])
    for r in estado.get('resultados', []):
        writer.writerow([
            r.get('arquivo', ''), r.get('tipo', ''), r.get('numero', ''), r.get('serie', ''),
            r.get('data', ''), r.get('operacao', ''), r.get('valor', ''), r.get('status', ''), r.get('chave', ''),
        ])
    for e in estado.get('erros_leitura', []):
        writer.writerow([e.get('arquivo', ''), '', '', '', '', '', '', e.get('mensagem', ''), ''])

    conteudo = '\ufeff' + saida.getvalue()
    return Response(
        conteudo,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="omnixml-{consulta_id[:8]}.csv"'},
    )


@app.delete('/api/consultas/<consulta_id>')
def excluir_consulta(consulta_id):
    try:
        pasta = _consulta_dir(consulta_id)
    except (ValueError, FileNotFoundError):
        return jsonify({'status': 'sucesso'})
    shutil.rmtree(pasta, ignore_errors=True)
    return jsonify({'status': 'sucesso'})


@app.errorhandler(413)
def arquivo_muito_grande(_):
    return jsonify({'status': 'erro', 'mensagem': 'Envio acima do limite de 200 MB por consulta.'}), 413
