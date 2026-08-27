import csv
import io
import json
import re
import shutil
import tempfile
import time
import uuid
import zipfile
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request
from defusedxml import ElementTree as ET

from core.factory import ArquivoInfo, ParserFactory
from core.validador import json_safe
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
    tmp.write_text(json.dumps(json_safe(estado), ensure_ascii=False, indent=2), encoding='utf-8')
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
    arquivos.append({
        'nome': Path(nome_original).name or 'documento.xml',
        'caminho_original': nome_original,
        'stored': identificador,
        'size': len(conteudo),
    })


def _adicionar_upload(pasta: Path, upload, arquivos: list, avisos: list) -> None:
    nome = upload.filename or ''
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
                        _novo_xml(pasta, info.filename, zf.read(info), arquivos)
                    except ValueError as exc:
                        if '500 MB' in str(exc) or '5000' in str(exc):
                            raise
                        avisos.append(str(exc))
        except zipfile.BadZipFile:
            raise ValueError(f'{Path(nome).name}: ZIP inválido ou corrompido.')
        return

    avisos.append(f'{Path(nome).name}: formato ignorado; use XML ou ZIP.')


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


def _dashboard_payload(estado: dict) -> dict:
    resultados = estado.get('resultados', [])
    erros_leitura = list(estado.get('erros_leitura', []))

    canceladas = {
        r.get('chave')
        for r in resultados
        if r.get('tipo') == 'Evento de cancelamento NF-e'
        and r.get('status') == 'Cancelamento confirmado'
        and r.get('chave')
    }

    notas = []
    duplicidades = []
    por_chave = {}
    for original in resultados:
        if original.get('tipo') in {'Evento de cancelamento NF-e', 'Desconhecido'}:
            continue
        nota = dict(original)
        chave = nota.get('chave') or ''
        if chave and chave in por_chave:
            duplicidades.append({
                'chave': chave,
                'arquivo_original': por_chave[chave].get('arquivo', ''),
                'arquivo_duplicado': nota.get('arquivo', ''),
            })
            continue
        if chave:
            por_chave[chave] = nota
        if chave in canceladas:
            nota['status'] = 'Cancelado'
        notas.append(nota)

    resumo_cfop = {}
    resumo_cst = {}
    resumo_serie = {}
    faturamento_diario = {}
    auditoria_tributaria = {}
    validacao_produtos = {}

    cfops_st = {'5405', '5403', '5401', '6404', '6403', '6401'}
    cst_csosn_st = {'60', '060', '500', '201', '202', '203'}

    for info in notas:
        cancelada = 'Cancelado' in str(info.get('status', ''))
        valor_nota = float(info.get('valor') or 0)
        operacao = info.get('operacao', 'Saída')
        tipo = info.get('tipo', '')
        serie = info.get('serie', 'N/A')
        itens = info.get('itens') or []

        if not cancelada and valor_nota > 0:
            if operacao == 'Saída':
                data_emissao = info.get('data') or 'N/A'
                tem_cfop_faturamento = any(item.get('cfop', '') in {'5929', '6929'} for item in itens)
                if not tem_cfop_faturamento:
                    faturamento_diario[data_emissao] = faturamento_diario.get(data_emissao, 0.0) + valor_nota

                chave_serie = f'{tipo}_{serie}'
                resumo_serie.setdefault(chave_serie, {'tipo': tipo, 'serie': serie, 'valor': 0.0})
                resumo_serie[chave_serie]['valor'] += valor_nota

            for item in itens:
                cfop = str(item.get('cfop', '') or '')
                cst = str(item.get('cst', '') or '')
                val = float(item.get('valor') or 0)
                ncm = str(item.get('ncm', '') or '')
                nome = str(item.get('nome', '') or '')
                codigo = str(item.get('codigo') or item.get('cprod') or 'S/C')

                if operacao == 'Saída':
                    chave_cfop = f'{tipo}_{cfop}'
                    resumo_cfop.setdefault(chave_cfop, {'tipo': tipo, 'cfop': cfop, 'valor': 0.0})
                    resumo_cfop[chave_cfop]['valor'] += val

                    chave_cst = f'{tipo}_{cst}'
                    resumo_cst.setdefault(chave_cst, {'tipo': tipo, 'cst': cst, 'valor': 0.0})
                    resumo_cst[chave_cst]['valor'] += val

                    chave_auditoria = f'{ncm}_{cfop}_{cst}'
                    if chave_auditoria not in auditoria_tributaria:
                        status = 'OK'
                        if len(ncm) != 8 or not ncm.isdigit():
                            status = 'NCM INVÁLIDO'
                        elif cfop in cfops_st and cst not in cst_csosn_st:
                            status = 'ALERTA: CFOP de ST com CST/CSOSN atípico'
                        elif cfop not in cfops_st and cst in cst_csosn_st:
                            status = 'ALERTA: CST/CSOSN de ST com CFOP a revisar'
                        auditoria_tributaria[chave_auditoria] = {
                            'ncm': ncm,
                            'cfop': cfop,
                            'cst': cst,
                            'status': status,
                            'valor': 0.0,
                            'operacao': operacao,
                        }
                    auditoria_tributaria[chave_auditoria]['valor'] += val

                if 'NFC-e' in tipo:
                    chave_prod = f'{codigo}_{cfop}_{cst}'
                    if chave_prod not in validacao_produtos:
                        status_prod = 'OK'
                        motivo = 'Sem divergências nas regras atualmente verificadas.'
                        if len(ncm) != 8 or not ncm.isdigit():
                            status_prod = 'Erro: NCM inválido'
                            motivo = 'O NCM deve possuir 8 dígitos numéricos.'
                        else:
                            nome_up = nome.upper()
                            is_combustivel = (
                                ncm.startswith('2710')
                                and any(t in nome_up for t in ['GASOLINA', 'DIESEL'])
                                and not any(sub in nome_up for sub in ['ADITIVO', 'FLUIDO', 'GRAXA', 'ARLA'])
                            )
                            if is_combustivel and cst not in {'60', '060', '04', '01', '61', '061'}:
                                status_prod = 'Alerta: Tributação Combustível'
                                motivo = f'O CST {cst} merece revisão para este produto.'
                        nome_limpo = re.sub(r'^B\d{2}[-\s]*', '', nome).strip()
                        validacao_produtos[chave_prod] = {
                            'codigo': codigo,
                            'ncm': ncm,
                            'produto': nome_limpo[:50],
                            'cfop': cfop,
                            'cst': cst,
                            'status': status_prod,
                            'motivo': motivo,
                        }

    lista_diario = [
        {'data': k, 'valor': round(v, 2)}
        for k, v in sorted(faturamento_diario.items())
    ]

    erros = []
    for erro in erros_leitura:
        erros.append({
            'arquivo': erro.get('arquivo', ''),
            'motivo': erro.get('mensagem', ''),
            'caminho': '',
        })

    notas_front = []
    for nota in notas:
        n = dict(nota)
        n.pop('itens', None)
        n.pop('validacoes', None)
        notas_front.append(n)

    return json_safe({
        'status': 'sucesso',
        'notas': notas_front,
        'cfop': [v for v in resumo_cfop.values() if v['valor'] > 0],
        'cst': [v for v in resumo_cst.values() if v['valor'] > 0],
        'serie': [v for v in resumo_serie.values() if v['valor'] > 0],
        'auditoria': list(auditoria_tributaria.values()),
        'diario': lista_diario,
        'produtos': list(validacao_produtos.values()),
        'erros': erros,
        'total_erros': len(erros),
        'total_lidos': len(estado.get('arquivos', [])),
        'duplicidades': duplicidades,
        'avisos': estado.get('avisos_upload', []),
    })


@app.before_request
def housekeeping():
    _limpar_expiradas()


@app.get('/')
def index():
    html = render_template('dashboard.html')
    ponte = '<script src="/static/web_bridge.js"></script>'
    return Response(html.replace('</body>', f'{ponte}</body>'), mimetype='text/html')


@app.get('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'OmniXML Web', 'storage': 'temporary'})


@app.post('/api/consultas')
def criar_consulta():
    uploads = request.files.getlist('arquivos')
    if not uploads or not any(a.filename for a in uploads):
        return jsonify({'status': 'erro', 'mensagem': 'Selecione XMLs, uma pasta ou um arquivo ZIP.'}), 400

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
        return jsonify({
            'status': 'erro',
            'mensagem': 'Nenhum XML utilizável foi encontrado.',
            'avisos': avisos,
        }), 400

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
    return jsonify({
        'status': 'sucesso',
        'consulta_id': consulta_id,
        'resumo': _resumo(estado),
        'avisos': avisos,
    })


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
            resultado = validar_documento(root, item['nome'])

            parser = ParserFactory.get_parser(root)
            if parser is not None and resultado.get('tipo') != 'Desconhecido':
                info = parser.extrair(root, ArquivoInfo(item['nome']))
                resultado['itens'] = json_safe(info.itens)

            estado['resultados'].append(resultado)
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
    return jsonify({
        'status': 'sucesso',
        'concluido': concluido,
        'resumo': _resumo(estado),
    })


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


@app.get('/api/consultas/<consulta_id>/dashboard')
def dashboard_consulta(consulta_id):
    try:
        pasta = _consulta_dir(consulta_id)
        estado = _carregar_estado(pasta)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 404
    return jsonify(_dashboard_payload(estado))


@app.get('/api/consultas/<consulta_id>/relatorio.csv')
def relatorio_csv(consulta_id):
    try:
        pasta = _consulta_dir(consulta_id)
        estado = _carregar_estado(pasta)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({'status': 'erro', 'mensagem': str(exc)}), 404

    dashboard = _dashboard_payload(estado)
    saida = io.StringIO()
    writer = csv.writer(saida, delimiter=';')
    writer.writerow(['Arquivo', 'Tipo', 'Numero', 'Serie', 'Data', 'Operacao', 'Valor', 'Status', 'Chave'])
    for r in dashboard.get('notas', []):
        writer.writerow([
            r.get('arquivo', ''), r.get('tipo', ''), r.get('numero', ''), r.get('serie', ''),
            r.get('data', ''), r.get('operacao', ''), r.get('valor', ''), r.get('status', ''), r.get('chave', ''),
        ])
    for e in dashboard.get('erros', []):
        writer.writerow([e.get('arquivo', ''), '', '', '', '', '', '', e.get('motivo', ''), ''])

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
