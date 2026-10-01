"""Read-only fiscal recovery. Secrets and intermediate responses stay in memory."""
import base64
import copy
import gzip
import io
import re
import ssl
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
from pathlib import Path

from lxml import etree

NS = 'http://www.portalfiscal.inf.br/nfe'
DS = 'http://www.w3.org/2000/09/xmldsig#'
SP_DOWNLOAD = 'https://nfce.fazenda.sp.gov.br/ws/NFCeDownloadXML.asmx'
SP_STATUS = 'https://nfce.fazenda.sp.gov.br/ws/NFeConsultaProtocolo4.asmx'
NATIONAL = 'https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx'
UF_CODES = {'RO':'11','AC':'12','AM':'13','RR':'14','PA':'15','AP':'16','TO':'17',
            'MA':'21','PI':'22','CE':'23','RN':'24','PB':'25','PE':'26','AL':'27','SE':'28','BA':'29',
            'MG':'31','ES':'32','RJ':'33','SP':'35','PR':'41','SC':'42','RS':'43','MS':'50','MT':'51','GO':'52','DF':'53'}
MAX_RESPONSE = 20 * 1024 * 1024


class RecoveryError(ValueError):
    def __init__(self, message, code='invalid', cooldown=False):
        super().__init__(message)
        self.code, self.cooldown = code, cooldown


def key_validate(value):
    key = re.sub(r'\s', '', value)
    if not re.fullmatch(r'[0-9]{44}', key):
        raise RecoveryError('A chave deve ter 44 dígitos.')
    total = sum(int(c) * (2 + i % 8) for i, c in enumerate(reversed(key[:-1])))
    check = 11 - total % 11
    if key[-1] != str(0 if check >= 10 else check):
        raise RecoveryError('Dígito verificador da chave inválido.')
    if key[:2] not in UF_CODES.values():
        raise RecoveryError('UF da chave inválida.')
    if key[20:22] == '65' and key[:2] == '35':
        return key, 'nfce-sp'
    if key[20:22] == '55':
        return key, 'nfe-national'
    raise RecoveryError('Cobertura: NF-e (55) nacional e NFC-e (65) de SP. Esta chave ainda não é atendida.', 'unsupported')


def parse_xml(data):
    if len(data) > MAX_RESPONSE:
        raise RecoveryError('Resposta excedeu o limite seguro.')
    try:
        root = etree.fromstring(data, parser=etree.XMLParser(resolve_entities=False, no_network=True))
        if root.getroottree().docinfo.doctype or any(isinstance(node, etree._Entity) for node in root.iter()):
            raise ValueError('DTD/entity forbidden')
        return root
    except Exception as exc:
        raise RecoveryError('XML da SEFAZ inválido ou inseguro.') from exc


def field(node, name):
    return (node.findtext('{%s}%s' % (NS, name)) or '').strip()


def returned(data, name):
    root = parse_xml(data)
    found = root.xpath('descendant-or-self::n:' + name, namespaces={'n': NS})
    if len(found) == 1:
        return found[0]
    # SOAP XmlNode/string may wrap an escaped XML payload. Bound recursion.
    for node in root.iter():
        text = (node.text or '').strip()
        if text.startswith('<') and name in text:
            nested = parse_xml(text.encode())
            found = nested.xpath('descendant-or-self::n:' + name, namespaces={'n': NS})
            if len(found) == 1:
                return found[0]
    raise RecoveryError('Resposta sem ' + name + ' reconhecido.')


def certificate_cnpj(data, password):
    from cryptography import x509
    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
    from cryptography.x509.oid import ObjectIdentifier
    try:
        private, cert, _ = load_key_and_certificates(data, password.encode() if password else None)
        if private is None or cert is None:
            raise ValueError()
        now = datetime.now(timezone.utc)
        if not cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
            raise RecoveryError('Certificado fora do período de validade.')
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        for other in san.get_values_for_type(x509.OtherName):
            if other.type_id == ObjectIdentifier('2.16.76.1.3.3'):
                # ICP-Brasil CNPJ is a single DER string; support short/long lengths.
                raw = other.value
                if len(raw) < 2 or raw[0] not in (0x0c, 0x13, 0x16, 0x04):
                    continue
                length, start = raw[1], 2
                if length & 0x80:
                    size = length & 0x7f
                    if size == 0 or size > 4 or len(raw) < 2 + size:
                        continue
                    length, start = int.from_bytes(raw[2:2+size], 'big'), 2 + size
                value = raw[start:start+length].decode('ascii').upper()
                if len(raw) == start + length and re.fullmatch(r'[A-Z0-9]{12}[0-9]{2}', value):
                    return value
        raise RecoveryError('Use um certificado A1 e-CNPJ com CNPJ ICP-Brasil identificado.')
    except RecoveryError:
        raise
    except Exception as exc:
        raise RecoveryError('Não foi possível abrir o A1. Confira o arquivo e a senha.') from exc


def processed(note, protocol, key, sae_protocol=''):
    info = note.findall('{%s}infNFe' % NS)
    prot = protocol.findall('{%s}infProt' % NS)
    if len(info) != 1 or info[0].get('Id') != 'NFe' + key or len(prot) != 1:
        raise RecoveryError('Chave ou estrutura do XML/protocolo divergente.')
    p = prot[0]
    required = ('tpAmb','verAplic','chNFe','dhRecbto','nProt','digVal','cStat','xMotivo')
    if any(not field(p, f) for f in required):
        raise RecoveryError('Protocolo de autorização incompleto.')
    ide = info[0].find('{%s}ide' % NS)
    if ide is None or field(ide, 'tpAmb') != '1' or field(ide, 'mod') != key[20:22]:
        raise RecoveryError('Modelo/ambiente da nota divergente.')
    if field(p,'chNFe') != key or field(p,'tpAmb') != '1' or field(p,'cStat') not in ('100','150'):
        raise RecoveryError('Protocolo não corresponde à autorização da chave em produção.')
    if sae_protocol and field(p,'nProt') != sae_protocol:
        raise RecoveryError('Protocolo da consulta diverge do download SAE.')
    refs = note.xpath('./ds:Signature/ds:SignedInfo/ds:Reference[@URI=$uri]/ds:DigestValue',
                      namespaces={'ds':DS}, uri='#NFe'+key)
    signatures = note.findall('{%s}Signature/{%s}SignatureValue' % (DS,DS))
    if len(refs) != 1 or (refs[0].text or '').strip() != field(p,'digVal') or len(signatures) != 1 or not signatures[0].text:
        raise RecoveryError('Assinatura ausente ou digest divergente do protocolo.')
    root = etree.Element('{%s}nfeProc' % NS, nsmap={None:NS}, versao='4.00')
    root.extend([copy.deepcopy(note), copy.deepcopy(protocol)])
    return etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=False)


def service_status(node, accepted):
    code, reason = field(node,'cStat'), field(node,'xMotivo')
    if code not in accepted:
        raise RecoveryError('SEFAZ ' + code + ': ' + reason[:300], code, code in ('137','656'))
    return code, reason


def unzip_document(text):
    try:
        compressed = base64.b64decode(text, validate=True)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            data = stream.read(MAX_RESPONSE + 1)
        return parse_xml(data)
    except RecoveryError:
        raise
    except Exception as exc:
        raise RecoveryError('Documento compactado da SEFAZ inválido.') from exc


def distribution_result(data, key):
    result = returned(data,'retDistDFeInt')
    code, reason = service_status(result, {'138'})
    documents = result.findall('{%s}loteDistDFeInt/{%s}docZip' % (NS,NS))
    if len(documents) > 50:
        raise RecoveryError('Quantidade de documentos inesperada.')
    for zipped in documents:
        node = unzip_document((zipped.text or '').strip())
        if node.tag == '{%s}nfeProc' % NS:
            notes, protocols = node.findall('{%s}NFe' % NS), node.findall('{%s}protNFe' % NS)
            if len(notes) == len(protocols) == 1:
                return processed(notes[0],protocols[0],key), code, reason
    raise RecoveryError('A SEFAZ retornou resumo/eventos, sem XML completo. Confira a permissão e a manifestação no seu sistema fiscal. Nenhum evento foi enviado.', 'summary')


def load_sp_server_trust(context):
    """Pinned public CAs published by SEFAZ/SP, never from a user's A1."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    bundle = (Path(__file__).resolve().parents[1] / 'certs' / 'sefaz-sp-ca.pem').read_bytes()
    certs = x509.load_pem_x509_certificates(bundle)
    pins = {
        '8e30f7f0b678ca1440a94a5be416bed9ae5aff7f0f2e08d4bbe28af2c8eb8660',
        '8606539037b8ff9d1eb2e8831312cbc667c824e9e5aa2dbb326172446f441e27',
        '6e0bff069a26994c15de2c4888cc54af84882e5495b7fbf66be9ccffec7489f6',
        '169cbf0547f3dfc4e63e4af9e0255a76037778ff5b8f4a536abdff3a91dfc3c5',
    }
    if len(certs) != len(pins) or {c.fingerprint(hashes.SHA256()).hex() for c in certs} != pins:
        raise RecoveryError('A cadeia pública SEFAZ/SP não corresponde à versão conferida.', 'ca_bundle')
    now = datetime.now(timezone.utc)
    for cert in certs:
        if not cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca:
            raise RecoveryError('Certificado da cadeia pública não é uma CA.', 'ca_bundle')
        if not cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
            raise RecoveryError('A cadeia pública SEFAZ/SP está fora da validade.', 'ca_bundle')
    root = next(c for c in certs if c.subject == c.issuer)
    root.verify_directly_issued_by(root)
    for cert in certs:
        if cert != root:
            cert.verify_directly_issued_by(root)
    context.load_verify_locations(cadata=bundle.decode('ascii'))


class FiscalClient:
    def __init__(self, data, password, provider=None):
        self.stage = "a1_tls"
        from requests import Session
        from requests_pkcs12 import Pkcs12Adapter
        deadline = time.monotonic() + 120
        class BoundedSession(Session):
            def request(self, method, url, **kwargs):
                address = urlsplit(url)
                if address.scheme != 'https' or address.hostname not in ('nfce.fazenda.sp.gov.br','www1.nfe.fazenda.gov.br') or address.port not in (None,443):
                    raise RecoveryError('Destino de serviço não permitido.')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RecoveryError('Tempo máximo de consulta atingido.')
                kwargs.update(allow_redirects=False, stream=True, timeout=(min(15,remaining),min(30,remaining)))
                response = super().request(method, url, **kwargs)
                try:
                    response.raise_for_status()
                    if response.is_redirect:
                        raise RecoveryError('Redirecionamento do serviço não permitido.')
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        if time.monotonic() > deadline:
                            raise RecoveryError('Tempo máximo de consulta atingido.')
                        size += len(chunk)
                        if size > MAX_RESPONSE:
                            raise RecoveryError('Resposta excedeu o limite seguro.')
                        chunks.append(chunk)
                    response._content = b''.join(chunks)
                    response._content_consumed = True
                    return response
                finally:
                    response.close()
        self.session = BoundedSession()
        self.session.trust_env = False
        try:
            adapter = Pkcs12Adapter(pkcs12_data=data, pkcs12_password=password)
            # The adapter creates a bare SSLContext. Explicitly load the system
            # store as well as Requests' CA bundle; never use the uploaded A1 as
            # a source of server trust anchors. No global SSL monkeypatch.
            adapter.ssl_context.load_default_certs(ssl.Purpose.SERVER_AUTH)
            from requests.certs import where
            adapter.ssl_context.load_verify_locations(cafile=where())
            adapter.ssl_context.verify_mode = ssl.CERT_REQUIRED
            adapter.ssl_context.check_hostname = True
            if provider == 'nfce-sp':
                load_sp_server_trust(adapter.ssl_context)
                self.session.mount('https://nfce.fazenda.sp.gov.br/',adapter)
            elif provider == 'nfe-national':
                self.session.mount('https://www1.nfe.fazenda.gov.br/',adapter)
            else:
                self.session.mount('https://',adapter)
        except Exception:
            self.session.close()
            raise

    def close(self):
        self.session.close()

    def query(self, endpoint, operation_filter, message, version, uf):
        from zeep import Client, Settings
        from zeep.transports import Transport
        from zeep.wsdl.bindings.soap import Soap11Binding, Soap12Binding
        self.stage = 'wsdl'
        client = Client(endpoint+'?WSDL', transport=Transport(session=self.session,timeout=45,operation_timeout=45),
                        settings=Settings(strict=True,raw_response=True,forbid_dtd=True,forbid_entities=True,forbid_external=True))
        options = []
        for service_name, service in client.wsdl.services.items():
            for port_name, port in service.ports.items():
                if isinstance(port.binding,(Soap11Binding,Soap12Binding)):
                    for name, op in port.binding._operations.items():
                        if operation_filter.lower() in name.lower():
                            options.append((0 if isinstance(port.binding,Soap12Binding) else 1,service_name,port_name,name,op))
        if not options:
            raise RecoveryError('Contrato SOAP não reconhecido.')
        _, service, port, name, op = sorted(options,key=lambda item:item[:4])[0]
        elements = list(op.input.body.type.elements)
        if len(elements) != 1:
            raise RecoveryError('Parâmetro SOAP inesperado.')
        param, element = elements[0]
        kind = element.type
        qname = getattr(kind,'qname',None)
        if qname is not None and qname.localname == 'string':
            value = etree.tostring(message,encoding='unicode')
        elif getattr(kind,'elements',None):
            if [n for n,_ in kind.elements] != ['_value_1']:
                raise RecoveryError('Parâmetro XML SOAP não reconhecido.')
            value = kind(_value_1=message)
        else:
            value = message
        arguments = {param:value}
        headers = list(op.input.header.type.elements) if op.input.header is not None else []
        if headers:
            values = {}
            for header_name, header in headers:
                fields = {n for n,_ in getattr(header.type,'elements',[])}
                if not fields.issubset({'cUF','versaoDados'}):
                    raise RecoveryError('Cabeçalho SOAP inesperado.')
                values[header_name] = header.type(**{n:uf if n == 'cUF' else version for n in fields})
            arguments['_soapheaders'] = values
        proxy = client.bind(service,port)
        proxy._binding_options['address'] = endpoint
        self.stage = 'soap'
        return proxy[name](**arguments).content


def message(name, version, fields):
    root = etree.Element('{%s}%s' % (NS,name),nsmap={None:NS},versao=version)
    for key,value in fields.items():
        etree.SubElement(root,'{%s}%s' % (NS,key)).text = value
    return root


def recover(client, key, provider, cnpj, uf, status_only=False):
    if provider == 'nfe-national':
        if status_only:
            raise RecoveryError('Consulta de situação disponível nesta versão para NFC-e/SP.', 'unsupported')
        req = message('distDFeInt','1.01',{'tpAmb':'1','cUFAutor':UF_CODES[uf],'CNPJ':cnpj})
        etree.SubElement(etree.SubElement(req,'{%s}consChNFe' % NS),'{%s}chNFe' % NS).text = key
        data = client.query(NATIONAL,'nfeDistDFeInteresse',req,'1.01',UF_CODES[uf])
        return distribution_result(data,key)
    req = message('consSitNFe','4.00',{'tpAmb':'1','xServ':'CONSULTAR','chNFe':key})
    consultation = returned(client.query(SP_STATUS,'consulta',req,'4.00','35'),'retConsSitNFe')
    code, reason = service_status(consultation,{'100','150','101','151'})
    if status_only:
        return None, code, reason
    req = message('nfceDownloadXML','1.00',{'tpAmb':'1','chNFCe':key})
    download = returned(client.query(SP_DOWNLOAD,'download',req,'1.00','35'),'retNfceDownloadXML')
    service_status(download,{'200'})
    notes = download.findall('.//{%s}NFe' % NS)
    protocols = consultation.findall('{%s}protNFe' % NS)
    sae = download.findall('.//{%s}nfeProc/{%s}nProt' % (NS,NS))
    if len(notes) != 1 or len(protocols) != 1 or len(sae) != 1 or not sae[0].text:
        raise RecoveryError('Retorno SAE/consulta incompleto. XML final não gerado.')
    output = processed(notes[0],protocols[0],key,sae[0].text.strip())
    if code in ('101','151'):
        reason += ' — CANCELADA; XML contém autorização original, sem evento de cancelamento.'
    return output, code, reason
