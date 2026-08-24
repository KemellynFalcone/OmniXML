import sys
from pathlib import Path
from decimal import Decimal
import xml.etree.ElementTree as StdET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.factory import ArquivoInfo, ParserFactory


NFE_BODY = '''<NFe{ns}>
  <infNFe Id="NFe{chave}">
    <ide><mod>55</mod><serie>1</serie><nNF>123</nNF><dhEmi>2026-08-01T10:00:00-03:00</dhEmi><tpNF>0</tpNF></ide>
    <emit><xNome>Empresa X</xNome></emit>
    <det nItem="1"><prod><cProd>ABC</cProd><xProd>Produto</xProd><NCM>12345678</NCM><CFOP>1102</CFOP><uCom>UN</uCom><qCom>2.0000</qCom><vProd>20.00</vProd><vDesc>1.00</vDesc></prod><imposto><ICMS><ICMS00><CST>00</CST></ICMS00></ICMS></imposto></det>
    <total><ICMSTot><vNF>19.00</vNF></ICMSTot></total>
  </infNFe>
</NFe>'''


def parse(xml):
    root = StdET.fromstring(xml)
    parser = ParserFactory.get_parser(root)
    assert parser is not None
    return parser.extrair(root, ArquivoInfo('teste.xml'))


def test_nfe_com_namespace():
    info = parse(NFE_BODY.format(ns=' xmlns="http://www.portalfiscal.inf.br/nfe"', chave='3'*44))
    assert info.numero_nota == '123'
    assert info.serie == '1'
    assert info.operacao == 'Entrada'
    assert info.valor == Decimal('19.00')
    assert info.itens[0]['codigo'] == 'ABC'
    assert info.itens[0]['valor'] == Decimal('19.00')


def test_nfe_sem_namespace():
    info = parse(NFE_BODY.format(ns='', chave='3'*44))
    assert info.numero_nota == '123'
    assert info.serie == '1'
    assert info.operacao == 'Entrada'
    assert info.emitente_nome == 'Empresa X'
    assert info.itens[0]['cfop'] == '1102'
    assert info.itens[0]['cst'] == '00'


def test_cancelamento_confirmado_por_conteudo():
    chave = '3' * 44
    xml = f'''<procEventoNFe xmlns="http://www.portalfiscal.inf.br/nfe">
      <evento><infEvento><chNFe>{chave}</chNFe><tpEvento>110111</tpEvento></infEvento></evento>
      <retEvento><infEvento><tpEvento>110111</tpEvento><chNFe>{chave}</chNFe><cStat>135</cStat><xMotivo>Evento registrado</xMotivo></infEvento></retEvento>
    </procEventoNFe>'''
    evento = ParserFactory.get_evento_cancelamento(StdET.fromstring(xml))
    assert evento is not None
    assert evento.chave == chave
    assert evento.confirmado is True


def test_evento_nao_confirmado_nao_cancela():
    chave = '3' * 44
    xml = f'''<evento xmlns="http://www.portalfiscal.inf.br/nfe"><infEvento><chNFe>{chave}</chNFe><tpEvento>110111</tpEvento></infEvento></evento>'''
    evento = ParserFactory.get_evento_cancelamento(StdET.fromstring(xml))
    assert evento is not None
    assert evento.confirmado is False
