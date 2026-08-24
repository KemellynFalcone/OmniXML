from dataclasses import dataclass, asdict
from typing import Optional

from core.factory import (
    ArquivoInfo,
    ParserFactory,
    find_child,
    find_descendant,
    text_of,
)


@dataclass
class ResultadoValidacao:
    codigo: str
    severidade: str
    mensagem: str
    campo: Optional[str] = None

    def to_dict(self):
        return asdict(self)


def calcular_dv_chave(chave_sem_dv: str) -> int:
    """Calcula o dígito verificador de uma chave fiscal de 44 posições."""
    if len(chave_sem_dv) != 43 or not chave_sem_dv.isdigit():
        raise ValueError("A base da chave deve possuir 43 dígitos numéricos.")

    peso = 2
    soma = 0
    for digito in reversed(chave_sem_dv):
        soma += int(digito) * peso
        peso += 1
        if peso > 9:
            peso = 2

    resto = soma % 11
    dv = 11 - resto
    return 0 if dv >= 10 else dv


def validar_chave_acesso(chave: str) -> list[ResultadoValidacao]:
    resultados: list[ResultadoValidacao] = []
    chave = (chave or "").strip()

    if not chave:
        return [ResultadoValidacao(
            codigo="CHAVE-001",
            severidade="ERRO",
            mensagem="Chave de acesso não encontrada no documento.",
            campo="infNFe/@Id",
        )]

    if len(chave) != 44 or not chave.isdigit():
        return [ResultadoValidacao(
            codigo="CHAVE-002",
            severidade="ERRO",
            mensagem="A chave de acesso deve possuir exatamente 44 dígitos numéricos.",
            campo="chave",
        )]

    esperado = calcular_dv_chave(chave[:43])
    informado = int(chave[43])
    if esperado != informado:
        resultados.append(ResultadoValidacao(
            codigo="CHAVE-003",
            severidade="ERRO",
            mensagem=f"Dígito verificador inválido: informado {informado}, esperado {esperado}.",
            campo="chave/cDV",
        ))
    else:
        resultados.append(ResultadoValidacao(
            codigo="CHAVE-000",
            severidade="OK",
            mensagem="Chave de acesso com 44 dígitos e DV válido.",
            campo="chave",
        ))

    return resultados


def validar_consistencia_chave_nfe(root, info: ArquivoInfo) -> list[ResultadoValidacao]:
    """Compara campos básicos da NF-e com as posições codificadas na chave."""
    chave = (info.chave or "").strip()
    if len(chave) != 44 or not chave.isdigit():
        return []

    resultados: list[ResultadoValidacao] = []
    inf_nfe = find_descendant(root, "infNFe")
    ide = find_child(inf_nfe, "ide") if inf_nfe is not None else None
    if ide is None:
        return resultados

    comparacoes = [
        ("mod", text_of(find_child(ide, "mod")), chave[20:22], "CHAVE-010", "modelo"),
        ("serie", text_of(find_child(ide, "serie")), str(int(chave[22:25])), "CHAVE-011", "série"),
        ("nNF", text_of(find_child(ide, "nNF")), str(int(chave[25:34])), "CHAVE-012", "número da nota"),
    ]

    for campo, xml_valor, chave_valor, codigo, descricao in comparacoes:
        if xml_valor and xml_valor.isdigit():
            normalizado = str(int(xml_valor))
            if normalizado != chave_valor:
                resultados.append(ResultadoValidacao(
                    codigo=codigo,
                    severidade="ERRO",
                    mensagem=f"O {descricao} do XML ({normalizado}) diverge da chave ({chave_valor}).",
                    campo=f"ide/{campo}",
                ))

    if not resultados:
        resultados.append(ResultadoValidacao(
            codigo="CHAVE-019",
            severidade="OK",
            mensagem="Modelo, série e número da NF-e são consistentes com a chave de acesso.",
            campo="ide",
        ))

    return resultados


def validar_protocolo(root) -> list[ResultadoValidacao]:
    inf_prot = find_descendant(root, "infProt")
    if inf_prot is None:
        return [ResultadoValidacao(
            codigo="SEFAZ-001",
            severidade="ALERTA",
            mensagem="Protocolo de autorização não encontrado. O XML pode ser uma NF-e sem nfeProc.",
            campo="protNFe/infProt",
        )]

    cstat = text_of(find_child(inf_prot, "cStat"))
    motivo = text_of(find_child(inf_prot, "xMotivo"))
    nprot = text_of(find_child(inf_prot, "nProt"))

    if cstat == "100":
        complemento = f" Protocolo: {nprot}." if nprot else ""
        return [ResultadoValidacao(
            codigo="SEFAZ-100",
            severidade="OK",
            mensagem=f"NF-e autorizada pela SEFAZ.{complemento}",
            campo="protNFe/infProt/cStat",
        )]

    if not cstat:
        return [ResultadoValidacao(
            codigo="SEFAZ-002",
            severidade="ALERTA",
            mensagem="Protocolo encontrado, porém sem cStat.",
            campo="protNFe/infProt/cStat",
        )]

    return [ResultadoValidacao(
        codigo=f"SEFAZ-{cstat}",
        severidade="ERRO",
        mensagem=f"Documento sem autorização cStat=100. Retorno: {cstat} - {motivo or 'motivo não informado'}.",
        campo="protNFe/infProt/cStat",
    )]


def validar_documento(root, nome_arquivo: str) -> dict:
    evento = ParserFactory.get_evento_cancelamento(root)
    if evento is not None:
        return {
            "arquivo": nome_arquivo,
            "tipo": "Evento de cancelamento NF-e",
            "chave": evento.chave,
            "status": "Cancelamento confirmado" if evento.confirmado else "Evento não confirmado",
            "validacoes": [ResultadoValidacao(
                codigo=f"EVENTO-{evento.cstat or 'SEM-CSTAT'}",
                severidade="OK" if evento.confirmado else "ALERTA",
                mensagem=evento.motivo or "Evento de cancelamento identificado.",
                campo="evento/infEvento",
            ).to_dict()],
        }

    parser = ParserFactory.get_parser(root)
    if parser is None:
        return {
            "arquivo": nome_arquivo,
            "tipo": "Desconhecido",
            "chave": "",
            "status": "Não reconhecido",
            "validacoes": [ResultadoValidacao(
                codigo="XML-002",
                severidade="ERRO",
                mensagem="Formato de documento fiscal não reconhecido.",
            ).to_dict()],
        }

    info = parser.extrair(root, ArquivoInfo(nome_arquivo))
    resultados: list[ResultadoValidacao] = [ResultadoValidacao(
        codigo="XML-000",
        severidade="OK",
        mensagem="XML bem-formado e documento fiscal reconhecido.",
    )]

    if "NF-e" in info.tipo or "NFC-e" in info.tipo:
        resultados.extend(validar_chave_acesso(info.chave))
        resultados.extend(validar_consistencia_chave_nfe(root, info))
        resultados.extend(validar_protocolo(root))

    severidades = {r.severidade for r in resultados}
    if "ERRO" in severidades:
        status = "Com erros"
    elif "ALERTA" in severidades:
        status = "Com alertas"
    else:
        status = "Conforme às regras verificadas"

    return {
        "arquivo": nome_arquivo,
        "tipo": info.tipo,
        "chave": info.chave,
        "numero": info.numero_nota,
        "serie": info.serie,
        "data": info.data,
        "operacao": info.operacao,
        "valor": float(info.valor),
        "emitente": info.emitente_nome,
        "status": status,
        "validacoes": [resultado.to_dict() for resultado in resultados],
    }
