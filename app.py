from flask import Flask, render_template, jsonify
from core.factory import ParserFactory, ArquivoInfo
from core.validador import json_safe
from defusedxml import ElementTree as ET
import os
import tkinter as tk
from tkinter import filedialog
import re
import threading
import webbrowser
from time import sleep

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 

NAMESPACE = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

PROCESSAMENTO = {
    'arquivos': [],
    'total': 0,
    'processados': 0,
    'notas_validas': {},
    'eventos_cancelamento': [],
    'duplicidades': [],
    'arquivos_com_erro': [],
    'total_erros': 0
}

def registrar_erro(nome, motivo, caminho):
    global PROCESSAMENTO
    PROCESSAMENTO['total_erros'] += 1
    if len(PROCESSAMENTO['arquivos_com_erro']) < 150:
        PROCESSAMENTO['arquivos_com_erro'].append({
            "arquivo": nome,
            "motivo": motivo,
            "caminho": caminho
        })

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/limpar_sessao', methods=['GET'])
def limpar_sessao():
    global PROCESSAMENTO
    PROCESSAMENTO = {
        'arquivos': [],
        'total': 0,
        'processados': 0,
        'notas_validas': {},
        'eventos_cancelamento': [],
        'duplicidades': [],
        'arquivos_com_erro': [],
        'total_erros': 0
    }
    return jsonify({"status": "sucesso"})

@app.route('/selecionar_pasta', methods=['GET'])
def selecionar_pasta():
    global PROCESSAMENTO
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    pasta_base = filedialog.askdirectory(title="Selecione a pasta raiz dos XMLs do cliente")
    root.destroy()

    if not pasta_base:
        return jsonify({"status": "cancelado"})

    arquivos_xml = []
    for raiz, dirs, files in os.walk(pasta_base):
        for f in files:
            if f.lower().endswith('.xml'):
                arquivos_xml.append(os.path.join(raiz, f))

    PROCESSAMENTO['arquivos'] = arquivos_xml
    PROCESSAMENTO['total'] = len(arquivos_xml)
    PROCESSAMENTO['processados'] = 0
    PROCESSAMENTO['notas_validas'] = {}
    PROCESSAMENTO['eventos_cancelamento'] = []
    PROCESSAMENTO['duplicidades'] = []
    PROCESSAMENTO['arquivos_com_erro'] = []
    PROCESSAMENTO['total_erros'] = 0

    return jsonify({"status": "sucesso", "total": PROCESSAMENTO['total']})

@app.route('/processar_lote', methods=['GET'])
def processar_lote():
    global PROCESSAMENTO

    lote = PROCESSAMENTO['arquivos'][:1000]
    PROCESSAMENTO['arquivos'] = PROCESSAMENTO['arquivos'][1000:]

    for caminho_completo in lote:
        nome_arquivo = os.path.basename(caminho_completo)
        try:
            tree = ET.parse(caminho_completo)
            root_xml = tree.getroot()

            evento = ParserFactory.get_evento_cancelamento(root_xml)
            if evento is not None:
                PROCESSAMENTO['eventos_cancelamento'].append({
                    'arquivo': nome_arquivo,
                    'caminho': caminho_completo,
                    'evento': evento,
                })
            else:
                parser = ParserFactory.get_parser(root_xml)
                if parser is None:
                    registrar_erro(nome_arquivo, "Formato de XML fiscal não reconhecido", caminho_completo)
                else:
                    info = parser.extrair(root_xml, ArquivoInfo(nome_arquivo))
                    chave = info.chave or info.arquivo

                    if chave in PROCESSAMENTO['notas_validas']:
                        anterior = PROCESSAMENTO['notas_validas'][chave]
                        PROCESSAMENTO['duplicidades'].append({
                            'chave': chave,
                            'arquivo_original': anterior.arquivo,
                            'arquivo_duplicado': nome_arquivo,
                            'caminho_duplicado': caminho_completo,
                        })
                        registrar_erro(
                            nome_arquivo,
                            f"Chave duplicada; documento original: {anterior.arquivo}",
                            caminho_completo,
                        )
                    else:
                        PROCESSAMENTO['notas_validas'][chave] = info

        except ET.ParseError:
            registrar_erro(nome_arquivo, "Arquivo corrompido ou malformado (XML inválido)", caminho_completo)
        except Exception as e:
            registrar_erro(nome_arquivo, f"Erro inesperado de leitura: {str(e)}", caminho_completo)

        PROCESSAMENTO['processados'] += 1

    return jsonify({
        "processados": PROCESSAMENTO['processados'],
        "total": PROCESSAMENTO['total']
    })

@app.route('/finalizar_processamento', methods=['GET'])
def finalizar_processamento():
    global PROCESSAMENTO

    # Aplica somente cancelamentos confirmados pela resposta da SEFAZ.
    for registro in PROCESSAMENTO['eventos_cancelamento']:
        evento = registro['evento']
        if evento.confirmado and evento.chave in PROCESSAMENTO['notas_validas']:
            nota = PROCESSAMENTO['notas_validas'][evento.chave]
            nota.status = 'Cancelado'
            nota.cancelado = True
        elif not evento.confirmado:
            registrar_erro(
                registro['arquivo'],
                f"Evento de cancelamento sem confirmação SEFAZ (cStat={evento.cstat or 'ausente'})",
                registro['caminho'],
            )

    resumo_cfop = {}
    resumo_cst = {}
    resumo_serie = {}
    faturamento_diario = {}
    auditoria_tributaria = {}
    validacao_produtos = {} 

    cfops_st = ['5405', '5403', '5401', '6404', '6403', '6401']
    cst_csosn_st = ['60', '060', '500', '201', '202', '203']

    for info in PROCESSAMENTO['notas_validas'].values():
        if not info.cancelado and info.valor > 0:
            if info.operacao == 'Saída':
                data_emissao = info.data
                
                tem_cfop_faturamento = any(item.get('cfop', '') in ['5929', '6929'] for item in info.itens)
                if not tem_cfop_faturamento:
                    faturamento_diario[data_emissao] = faturamento_diario.get(data_emissao, 0) + info.valor

                chave_serie = f"{info.tipo}_{info.serie}"
                if chave_serie not in resumo_serie:
                    resumo_serie[chave_serie] = {"tipo": info.tipo, "serie": info.serie, "valor": 0}
                resumo_serie[chave_serie]["valor"] += info.valor
            
            for item in info.itens:
                cfop = item.get('cfop', '')
                cst = item.get('cst', '')
                val = item.get('valor', 0.0)
                ncm = item.get('ncm', '')
                nome = item.get('nome', '')
                codigo = item.get('codigo', 'S/C')
                
                if info.operacao == 'Saída':
                    chave_cfop = f"{info.tipo}_{cfop}"
                    if chave_cfop not in resumo_cfop:
                        resumo_cfop[chave_cfop] = {"tipo": info.tipo, "cfop": cfop, "valor": 0}
                    resumo_cfop[chave_cfop]["valor"] += val

                    chave_cst = f"{info.tipo}_{cst}"
                    if chave_cst not in resumo_cst:
                        resumo_cst[chave_cst] = {"tipo": info.tipo, "cst": cst, "valor": 0}
                    resumo_cst[chave_cst]["valor"] += val

                    chave_auditoria = f"{ncm}_{cfop}_{cst}"
                    if chave_auditoria not in auditoria_tributaria:
                        status = "OK"
                        if len(ncm) != 8: status = "NCM INVÁLIDO"
                        elif cfop in cfops_st and cst not in cst_csosn_st: status = "ERRO: CFOP de ST com CST/CSOSN Tributado"
                        elif cfop not in cfops_st and cst in cst_csosn_st: status = "ERRO: CST/CSOSN de ST com CFOP Tributado"
                        auditoria_tributaria[chave_auditoria] = { "ncm": ncm, "cfop": cfop, "cst": cst, "status": status, "valor": 0, "operacao": info.operacao }
                    auditoria_tributaria[chave_auditoria]["valor"] += val

                if 'NFC-e' in info.tipo:
                    chave_prod = f"{codigo}_{cfop}_{cst}"
                    
                    if chave_prod not in validacao_produtos:
                        status_prod = "OK"
                        motivo = "Tributação validada sem divergências aparentes."
                        
                        if len(ncm) != 8: 
                            status_prod = "Erro: NCM Incompleto"
                            motivo = "Aviso da Sefaz: O NCM não possui 8 dígitos."
                        else:
                            nome_up = nome.upper()
                            is_combustivel = ncm.startswith('2710') and any(t in nome_up for t in ['GASOLINA', 'ETANOL', 'DIESEL']) and not any(sub in nome_up for sub in ['MAX DIESEL', 'ADITIVO', 'OLEO QUEIMADO', 'FLUIDO', 'GRAXA', 'ARLA'])
                            
                            if is_combustivel:
                                if cst not in ['60', '060', '04', '01', '61', '061']: 
                                    status_prod = "Alerta: Tributação Combustível"
                                    motivo = f"O CST {cst} é atípico para combustível de bomba. O correto geralmente é ICMS Monofásico (61) ou ST (60)."
                                else:
                                    motivo = f"Combustível de bomba validado com sucesso (CST {cst})."
                            else:
                                motivo = f"Produto de prateleira ou lubrificante validado (CST {cst})."
                        
                        nome_limpo = re.sub(r'^B\d{2}[-\s]*', '', nome).strip()

                        validacao_produtos[chave_prod] = {
                            "codigo": codigo,
                            "ncm": ncm,
                            "produto": nome_limpo[:50],
                            "cfop": cfop,
                            "cst": cst,
                            "status": status_prod,
                            "motivo": motivo
                        }

    lista_diario = [{"data": k, "valor": round(v, 2)} for k, v in sorted(faturamento_diario.items())]
    
    lista_notas_front = []
    for info in PROCESSAMENTO['notas_validas'].values():
        d = info.to_dict()
        d['chave'] = info.chave
        lista_notas_front.append(d)
                
    return jsonify(json_safe({
        "status": "sucesso", 
        "notas": lista_notas_front,
        "cfop": [v for v in resumo_cfop.values() if v["valor"] > 0],
        "cst": [v for v in resumo_cst.values() if v["valor"] > 0],
        "serie": [v for v in resumo_serie.values() if v["valor"] > 0],
        "auditoria": list(auditoria_tributaria.values()),
        "diario": lista_diario,
        "produtos": list(validacao_produtos.values()),
        "erros": PROCESSAMENTO['arquivos_com_erro'],
        "total_erros": PROCESSAMENTO['total_erros'],
        "total_lidos": PROCESSAMENTO['total'],
        "duplicidades": PROCESSAMENTO['duplicidades']
    }))

@app.route('/importar_sped', methods=['GET'])
def importar_sped():
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    arquivo_sped = filedialog.askopenfilename(title="Selecione o arquivo SPED Fiscal (.txt)", filetypes=[("Arquivo Texto", "*.txt")])
    root.destroy()

    if not arquivo_sped:
        return jsonify({"status": "cancelado"})

    total_nfe_ent = 0.0
    total_nfe_sai = 0.0
    total_nfce_sai = 0.0
    sped_detalhes = []

    try:
        with open(arquivo_sped, 'r', encoding='latin-1') as f:
            for linha in f:
                campos = linha.split('|')
                if len(campos) < 2: continue
                reg = campos[1].strip()
                
                if reg == 'C100':
                    ind_oper = campos[2].strip() if len(campos) > 2 else ''
                    cod_mod = campos[5].strip() if len(campos) > 5 else ''
                    sit_doc = campos[6].strip() if len(campos) > 6 else ''
                    num_doc = campos[8].strip() if len(campos) > 8 else ''
                    chave = campos[9].strip() if len(campos) > 9 else ''
                    vl_doc = campos[12].strip() if len(campos) > 12 else ''
                    
                    if sit_doc in ['00', '01', '08'] and vl_doc: 
                        val = float(vl_doc.replace(',', '.'))
                        if cod_mod == '55':
                            if ind_oper == '0': total_nfe_ent += val
                            elif ind_oper == '1': total_nfe_sai += val
                        elif cod_mod in ['65', '59']:
                            if ind_oper == '1': total_nfce_sai += val
                        
                        sped_detalhes.append({
                            "chave": chave, "numero": num_doc, "modelo": cod_mod,
                            "operacao": "Entrada" if ind_oper == "0" else "Saída", "valor": val
                        })
                            
                elif reg == 'C800':
                    cod_mod = campos[2].strip() if len(campos) > 2 else ''
                    sit_doc = campos[3].strip() if len(campos) > 3 else ''
                    num_doc = campos[4].strip() if len(campos) > 4 else ''
                    vl_doc = campos[8].strip() if len(campos) > 8 else ''
                    chave = campos[9].strip() if len(campos) > 9 else ''
                    
                    if sit_doc in ['00', '01', '08'] and cod_mod in ['65', '59'] and vl_doc:
                        val = float(vl_doc.replace(',', '.'))
                        total_nfce_sai += val
                        sped_detalhes.append({
                            "chave": chave, "numero": num_doc, "modelo": cod_mod,
                            "operacao": "Saída", "valor": val
                        })
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

    return jsonify({
        "status": "sucesso",
        "sped_nfe_ent": round(total_nfe_ent, 2),
        "sped_nfe_sai": round(total_nfe_sai, 2),
        "sped_nfce_sai": round(total_nfce_sai, 2),
        "sped_detalhes": sped_detalhes
    })

@app.route('/importar_sped_contribuicoes', methods=['GET'])
def importar_sped_contribuicoes():
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    arquivo_sped = filedialog.askopenfilename(title="Selecione o SPED PIS/COFINS (.txt)", filetypes=[("Arquivo Texto", "*.txt")])
    root.destroy()

    if not arquivo_sped:
        return jsonify({"status": "cancelado"})

    resumo_cst = {}
    total_receita = 0.0
    ind_oper_atual = ''

    try:
        with open(arquivo_sped, 'r', encoding='latin-1') as f:
            for linha in f:
                campos = linha.split('|')
                if len(campos) < 2: continue
                reg = campos[1].strip()

                if reg == 'C100':
                    ind_oper_atual = campos[2].strip() if len(campos) > 2 else ''
                
                elif reg == 'C175':
                    cst = campos[5].strip() if len(campos) > 5 else ''
                    vl_opr = float(campos[3].replace(',', '.')) if len(campos) > 3 and campos[3] else 0.0
                    vl_pis = float(campos[10].replace(',', '.')) if len(campos) > 10 and campos[10] else 0.0
                    
                    total_receita += vl_opr

                    if cst not in resumo_cst:
                        resumo_cst[cst] = {'cst': cst, 'vl_opr': 0.0, 'vl_pis': 0.0}
                    resumo_cst[cst]['vl_opr'] += vl_opr
                    resumo_cst[cst]['vl_pis'] += vl_pis

                elif reg == 'C170':
                    if ind_oper_atual == '1':
                        cst = campos[25].strip() if len(campos) > 25 else ''
                        vl_opr = float(campos[7].replace(',', '.')) if len(campos) > 7 and campos[7] else 0.0
                        vl_pis = float(campos[30].replace(',', '.')) if len(campos) > 30 and campos[30] else 0.0

                        if cst:
                            total_receita += vl_opr
                            if cst not in resumo_cst:
                                resumo_cst[cst] = {'cst': cst, 'vl_opr': 0.0, 'vl_pis': 0.0}
                            resumo_cst[cst]['vl_opr'] += vl_opr
                            resumo_cst[cst]['vl_pis'] += vl_pis

    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})

    lista_cst = sorted(list(resumo_cst.values()), key=lambda x: x['vl_opr'], reverse=True)

    return jsonify({
        "status": "sucesso",
        "total_receita": round(total_receita, 2),
        "csts": lista_cst
    })

def abrir_navegador():
    sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    threading.Thread(target=abrir_navegador).start()
    app.run(port=5000)