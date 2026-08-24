from defusedxml import ElementTree as ET

from core.validacao_documental import calcular_dv_chave, validar_documento


def montar_chave(base_43: str) -> str:
    return base_43 + str(calcular_dv_chave(base_43))


def test_calcula_dv_e_valida_nfe_autorizada():
    base = "3526081234567800012355001000000123112345678"
    chave = montar_chave(base)

    xml = f'''<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
      <NFe>
        <infNFe Id="NFe{chave}" versao="4.00">
          <ide>
            <mod>55</mod>
            <serie>{int(chave[22:25])}</serie>
            <nNF>{int(chave[25:34])}</nNF>
            <dhEmi>2026-08-24T12:00:00-03:00</dhEmi>
            <tpNF>1</tpNF>
          </ide>
          <emit><xNome>Empresa Teste</xNome></emit>
          <total><ICMSTot><vNF>100.00</vNF></ICMSTot></total>
        </infNFe>
      </NFe>
      <protNFe>
        <infProt><cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo><nProt>123</nProt></infProt>
      </protNFe>
    </nfeProc>'''

    resultado = validar_documento(ET.fromstring(xml), "teste.xml")
    codigos = {item["codigo"] for item in resultado["validacoes"]}

    assert resultado["status"] == "Conforme às regras verificadas"
    assert "CHAVE-000" in codigos
    assert "SEFAZ-100" in codigos


def test_detecta_chave_com_dv_invalido():
    chave = "35260812345678000123550010000001231123456789"
    xml = f'''<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
      <infNFe Id="NFe{chave}">
        <ide><mod>55</mod><serie>1</serie><nNF>123</nNF><tpNF>1</tpNF></ide>
      </infNFe>
    </NFe>'''

    resultado = validar_documento(ET.fromstring(xml), "invalida.xml")
    assert any(item["codigo"] == "CHAVE-003" for item in resultado["validacoes"])
    assert resultado["status"] == "Com erros"
