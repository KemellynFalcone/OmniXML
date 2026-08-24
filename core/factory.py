from decimal import Decimal, InvalidOperation
from dataclasses import dataclass


NAMESPACES = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
    'cte': 'http://www.portalfiscal.inf.br/cte',
    'mdfe': 'http://www.portalfiscal.inf.br/mdfe',
}


def local_name(tag):
    """Retorna o nome local de uma tag XML, ignorando namespace."""
    if not tag:
        return ''
    return tag.rsplit('}', 1)[-1]


def find_descendant(element, name):
    """Busca o primeiro descendente pelo nome local, com ou sem namespace."""
    if element is None:
        return None
    for node in element.iter():
        if local_name(node.tag) == name:
            return node
    return None


def find_child(element, name):
    """Busca apenas filho direto pelo nome local, com ou sem namespace."""
    if element is None:
        return None
    for node in list(element):
        if local_name(node.tag) == name:
            return node
    return None


def find_all_descendants(element, name):
    if element is None:
        return []
    return [node for node in element.iter() if local_name(node.tag) == name]


def text_of(element, default=''):
    if element is None or element.text is None:
        return default
    return element.text.strip()


def decimal_of(element, default=Decimal('0')):
    value = text_of(element)
    if not value:
        return default
    try:
        return Decimal(value.replace(',', '.'))
    except InvalidOperation:
        return default


class ArquivoInfo:
    def __init__(self, arquivo):
        self.arquivo = arquivo
        self.chave = ''
        self.numero_nota = 'N/A'
        self.serie = 'N/A'
        self.data = 'N/A'
        self.valor = Decimal('0')
        self.tipo = 'Documento'
        self.operacao = 'Saída'
        self.status = 'OK'
        self.emitente_nome = 'Desconhecido'
        self.cancelado = False
        self.itens = []

    def to_dict(self):
        return {
            'numero_nota': self.numero_nota,
            'arquivo': self.arquivo,
            'serie': self.serie,
            'data': self.data,
            'valor': float(self.valor),
            'tipo': self.tipo,
            'operacao': self.operacao,
            'status': self.status,
            'emitente_nome': self.emitente_nome,
        }


@dataclass(frozen=True)
class EventoCancelamento:
    chave: str
    confirmado: bool
    cstat: str = ''
    motivo: str = ''


class ParserFactory:
    TIPOS_NFE = {'NFe', 'nfeProc'}
    TIPOS_CTE = {'CTe', 'cteProc'}
    TIPOS_MDFE = {'MDFe', 'mdfeProc'}
    TIPOS_CFE = {'CFe', 'CFeSat', 'CFeSAT'}
    TIPOS_EVENTO_NFE = {'evento', 'procEventoNFe', 'retEvento'}

    @staticmethod
    def get_parser(root):
        tipo = local_name(root.tag)
        if tipo in ParserFactory.TIPOS_NFE:
            return ParserNFe()
        if tipo in ParserFactory.TIPOS_CTE:
            return ParserCTe()
        if tipo in ParserFactory.TIPOS_MDFE:
            return ParserMDFe()
        if tipo in ParserFactory.TIPOS_CFE:
            return ParserCFeSAT()
        return None

    @staticmethod
    def get_evento_cancelamento(root):
        """Identifica cancelamento de NF-e pelo conteúdo do XML, nunca pelo caminho."""
        tipo = local_name(root.tag)
        if tipo not in ParserFactory.TIPOS_EVENTO_NFE:
            return None

        inf_evento = find_descendant(root, 'infEvento')
        if inf_evento is None:
            return None

        tp_evento = text_of(find_child(inf_evento, 'tpEvento'))
        if tp_evento != '110111':
            return None

        chave = text_of(find_child(inf_evento, 'chNFe'))
        if not chave:
            return None

        # Em procEventoNFe, o retorno da SEFAZ aparece em retEvento/infEvento.
        cstat = ''
        motivo = ''
        for node in find_all_descendants(root, 'infEvento'):
            candidate = text_of(find_child(node, 'cStat'))
            if candidate:
                cstat = candidate
                motivo = text_of(find_child(node, 'xMotivo'))

        # 135 = evento registrado e vinculado; 155 = cancelamento homologado fora de prazo.
        confirmado = cstat in {'135', '155'}
        return EventoCancelamento(chave=chave, confirmado=confirmado, cstat=cstat, motivo=motivo)


class ParserNFe:
    def extrair(self, root, info):
        inf_nfe = find_descendant(root, 'infNFe')
        if inf_nfe is None:
            return info

        chave_attr = inf_nfe.attrib.get('Id', '')
        if chave_attr.startswith('NFe'):
            info.chave = chave_attr[3:]
        elif chave_attr:
            info.chave = chave_attr

        ide = find_child(inf_nfe, 'ide')
        if ide is not None:
            modelo = text_of(find_child(ide, 'mod'))
            info.tipo = 'NFC-e (Mod. 65)' if modelo == '65' else 'NF-e (Mod. 55)'

            tp_nf = text_of(find_child(ide, 'tpNF'))
            if tp_nf in {'0', '1'}:
                info.operacao = 'Entrada' if tp_nf == '0' else 'Saída'

            numero = text_of(find_child(ide, 'nNF'))
            serie = text_of(find_child(ide, 'serie'))
            emissao = text_of(find_child(ide, 'dhEmi')) or text_of(find_child(ide, 'dEmi'))
            if numero:
                info.numero_nota = numero
            if serie:
                info.serie = serie
            if emissao:
                info.data = emissao[:10]

        emit = find_child(inf_nfe, 'emit')
        nome_emitente = text_of(find_child(emit, 'xNome'))
        if nome_emitente:
            info.emitente_nome = nome_emitente

        icms_tot = find_descendant(inf_nfe, 'ICMSTot')
        if icms_tot is not None:
            info.valor = decimal_of(find_child(icms_tot, 'vNF'))

        for det in find_all_descendants(inf_nfe, 'det'):
            prod = find_child(det, 'prod')
            if prod is None:
                continue

            valor_produto = decimal_of(find_child(prod, 'vProd'))
            desconto = decimal_of(find_child(prod, 'vDesc'))
            prod_info = {
                'codigo': text_of(find_child(prod, 'cProd'), 'N/A'),
                'cprod': text_of(find_child(prod, 'cProd'), 'N/A'),  # compatibilidade temporária
                'nome': text_of(find_child(prod, 'xProd'), 'N/A'),
                'ncm': text_of(find_child(prod, 'NCM'), 'N/A'),
                'unidade': text_of(find_child(prod, 'uCom'), 'N/A'),
                'cfop': text_of(find_child(prod, 'CFOP'), 'N/A'),
                'cst': 'N/A',
                'qtd': decimal_of(find_child(prod, 'qCom')),
                'valor_bruto': valor_produto,
                'desconto': desconto,
                'valor': valor_produto - desconto,
            }

            icms = find_descendant(det, 'ICMS')
            if icms is not None:
                for grupo in list(icms):
                    cst = text_of(find_child(grupo, 'CST'))
                    csosn = text_of(find_child(grupo, 'CSOSN'))
                    if cst:
                        prod_info['cst'] = cst
                        break
                    if csosn:
                        prod_info['cst'] = csosn
                        break

            info.itens.append(prod_info)

        return info


class ParserCTe:
    def extrair(self, root, info):
        info.tipo = 'CT-e (Mod. 57)'
        info.valor = decimal_of(find_descendant(root, 'vTPrest'))
        inf_cte = find_descendant(root, 'infCte')
        if inf_cte is not None:
            chave_attr = inf_cte.attrib.get('Id', '')
            info.chave = chave_attr[3:] if chave_attr.startswith('CTe') else chave_attr
            ide = find_child(inf_cte, 'ide')
            numero = text_of(find_child(ide, 'nCT'))
            serie = text_of(find_child(ide, 'serie'))
            emissao = text_of(find_child(ide, 'dhEmi'))
            if numero:
                info.numero_nota = numero
            if serie:
                info.serie = serie
            if emissao:
                info.data = emissao[:10]
        return info


class ParserMDFe:
    def extrair(self, root, info):
        info.tipo = 'MDF-e (Mod. 58)'
        info.valor = decimal_of(find_descendant(root, 'vCarga'))
        inf_mdfe = find_descendant(root, 'infMDFe')
        if inf_mdfe is not None:
            chave_attr = inf_mdfe.attrib.get('Id', '')
            info.chave = chave_attr[4:] if chave_attr.startswith('MDFe') else chave_attr
        return info


class ParserCFeSAT:
    def extrair(self, root, info):
        info.tipo = 'CF-e SAT (Mod. 59)'
        info.valor = decimal_of(find_descendant(root, 'vCFe'))
        return info
