import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module


def nfe_xml(chave, tp_nf='0'):
    return f'''<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe Id="NFe{chave}"><ide><mod>55</mod><serie>1</serie><nNF>123</nNF><dhEmi>2026-08-01T10:00:00-03:00</dhEmi><tpNF>{tp_nf}</tpNF></ide><emit><xNome>Empresa X</xNome></emit><det nItem="1"><prod><cProd>A1</cProd><xProd>Produto</xProd><NCM>12345678</NCM><CFOP>1102</CFOP><uCom>UN</uCom><qCom>1</qCom><vProd>10.00</vProd></prod><imposto><ICMS><ICMS00><CST>00</CST></ICMS00></ICMS></imposto></det><total><ICMSTot><vNF>10.00</vNF></ICMSTot></total></infNFe></NFe></nfeProc>'''


def cancel_xml(chave):
    return f'''<procEventoNFe xmlns="http://www.portalfiscal.inf.br/nfe"><evento><infEvento><chNFe>{chave}</chNFe><tpEvento>110111</tpEvento></infEvento></evento><retEvento><infEvento><tpEvento>110111</tpEvento><chNFe>{chave}</chNFe><cStat>135</cStat><xMotivo>Evento registrado</xMotivo></infEvento></retEvento></procEventoNFe>'''


def reset(paths):
    app_module.PROCESSAMENTO = {
        'arquivos': [str(p) for p in paths],
        'total': len(paths),
        'processados': 0,
        'notas_validas': {},
        'eventos_cancelamento': [],
        'duplicidades': [],
        'arquivos_com_erro': [],
        'total_erros': 0,
    }


def test_operacao_vem_do_xml_e_nao_da_pasta(tmp_path):
    pasta = tmp_path / 'saida_por_nome'
    pasta.mkdir()
    arquivo = pasta / 'nota.xml'
    arquivo.write_text(nfe_xml('1' * 44, tp_nf='0'), encoding='utf-8')
    reset([arquivo])

    client = app_module.app.test_client()
    client.get('/processar_lote')
    dados = client.get('/finalizar_processamento').get_json()

    assert dados['notas'][0]['operacao'] == 'Entrada'


def test_cancelamento_independe_do_nome_da_pasta(tmp_path):
    chave = '2' * 44
    nota = tmp_path / 'nota.xml'
    evento = tmp_path / 'evento_generico.xml'
    nota.write_text(nfe_xml(chave, tp_nf='1'), encoding='utf-8')
    evento.write_text(cancel_xml(chave), encoding='utf-8')
    reset([nota, evento])

    client = app_module.app.test_client()
    client.get('/processar_lote')
    dados = client.get('/finalizar_processamento').get_json()

    assert dados['notas'][0]['status'] == 'Cancelado'


def test_duplicidade_e_registrada_sem_sobrescrever(tmp_path):
    chave = '4' * 44
    a = tmp_path / 'a.xml'
    b = tmp_path / 'b.xml'
    a.write_text(nfe_xml(chave), encoding='utf-8')
    b.write_text(nfe_xml(chave), encoding='utf-8')
    reset([a, b])

    client = app_module.app.test_client()
    client.get('/processar_lote')
    dados = client.get('/finalizar_processamento').get_json()

    assert len(dados['notas']) == 1
    assert len(dados['duplicidades']) == 1
    assert dados['duplicidades'][0]['arquivo_original'] == 'a.xml'
    assert dados['duplicidades'][0]['arquivo_duplicado'] == 'b.xml'
