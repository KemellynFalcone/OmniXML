"""Synthetic fiscal data only; no real certificates or SEFAZ requests."""
import base64
import gzip
from datetime import datetime, timedelta, timezone

import pytest
from lxml import etree

from services import sefaz_download as fiscal


def key(model='65', uf='35'):
    initial = uf + '2609' + '12345678000195' + model + '002' + '000029794' + '1' + '00114687'
    total = sum(int(c)*(2+i%8) for i,c in enumerate(reversed(initial)))
    check = 11-total%11
    return initial + str(0 if check >= 10 else check)


def note_and_protocol(k=None):
    k = k or key()
    note = fiscal.parse_xml(f'''<NFe xmlns="{fiscal.NS}"><infNFe Id="NFe{k}" versao="4.00"><ide><mod>{k[20:22]}</mod><tpAmb>1</tpAmb></ide></infNFe><Signature xmlns="{fiscal.DS}"><SignedInfo><Reference URI="#NFe{k}"><DigestValue>c3ludGhldGlj</DigestValue></Reference></SignedInfo><SignatureValue>c3ludGhldGlj</SignatureValue></Signature></NFe>'''.encode())
    protocol = fiscal.parse_xml(f'''<protNFe xmlns="{fiscal.NS}" versao="4.00"><infProt><tpAmb>1</tpAmb><verAplic>TEST</verAplic><chNFe>{k}</chNFe><dhRecbto>2026-09-01T00:00:00-03:00</dhRecbto><nProt>135260000000001</nProt><digVal>c3ludGhldGlj</digVal><cStat>100</cStat><xMotivo>Autorizado</xMotivo></infProt></protNFe>'''.encode())
    return note, protocol


def envelope(name, fields, children=()):
    root = fiscal.message(name,'1.00',fields)
    root.extend(children)
    return etree.tostring(root)


@pytest.mark.parametrize('model,uf,provider',[('65','35','nfce-sp'),('55','35','nfe-national'),('55','13','nfe-national'),('55','53','nfe-national')])
def test_supported_keys(model,uf,provider):
    assert fiscal.key_validate(key(model,uf)) == (key(model,uf),provider)


@pytest.mark.parametrize('value',['','1'*44,key()[:-1]+'9',key('57'),key('55','99'),'١'*44])
def test_invalid_or_unsupported_keys(value):
    with pytest.raises(fiscal.RecoveryError):
        fiscal.key_validate(value)


def test_processed_preserves_note_and_real_protocol():
    note, protocol = note_and_protocol()
    result = fiscal.parse_xml(fiscal.processed(note,protocol,key(),'135260000000001'))
    assert result.tag == '{%s}nfeProc' % fiscal.NS
    assert len(result) == 2
    assert etree.tostring(result[0]) == etree.tostring(note)
    assert etree.tostring(result[1]) == etree.tostring(protocol)


@pytest.mark.parametrize('name,value',[('chNFe','0'*44),('tpAmb','2'),('cStat','101'),('digVal','different'),('nProt','')])
def test_divergent_protocol_rejected(name,value):
    note,protocol = note_and_protocol()
    protocol.find('.//{%s}%s' % (fiscal.NS,name)).text = value
    with pytest.raises(fiscal.RecoveryError):
        fiscal.processed(note,protocol,key())


def test_sae_protocol_must_match():
    note,protocol = note_and_protocol()
    with pytest.raises(fiscal.RecoveryError):
        fiscal.processed(note,protocol,key(),'wrong')


@pytest.mark.parametrize('xml',[b'<!DOCTYPE a [<!ENTITY e "secret">]><a>&e;</a>',b'<!DOCTYPE a SYSTEM "file:///etc/passwd"><a/>',b'<broken',b'\x00'])
def test_xml_rejects_dtd_entities_and_malformed(xml):
    with pytest.raises(fiscal.RecoveryError):
        fiscal.parse_xml(xml)


def test_escaped_soap_return():
    payload = envelope('retConsSitNFe',{'cStat':'100'})
    root = etree.Element('wrapper'); root.text = payload.decode()
    assert fiscal.field(fiscal.returned(etree.tostring(root),'retConsSitNFe'),'cStat') == '100'


def test_distribution_complete_note_and_summary():
    k = key('55')
    note,protocol = note_and_protocol(k)
    result = fiscal.processed(note,protocol,k)
    batch = etree.Element('{%s}loteDistDFeInt' % fiscal.NS)
    document = etree.SubElement(batch,'{%s}docZip' % fiscal.NS)
    document.text = base64.b64encode(gzip.compress(result)).decode()
    data = envelope('retDistDFeInt',{'cStat':'138','xMotivo':'Localizado'},[batch])
    output,code,_ = fiscal.distribution_result(data,k)
    assert code == '138' and fiscal.parse_xml(output)[0].tag.endswith('NFe')
    document.text = base64.b64encode(gzip.compress(f'<resNFe xmlns="{fiscal.NS}"/>'.encode())).decode()
    with pytest.raises(fiscal.RecoveryError) as error:
        fiscal.distribution_result(envelope('retDistDFeInt',{'cStat':'138'},[batch]),k)
    assert error.value.code == 'summary'


def test_compressed_size_limit(monkeypatch):
    monkeypatch.setattr(fiscal,'MAX_RESPONSE',100)
    with pytest.raises(fiscal.RecoveryError):
        fiscal.unzip_document(base64.b64encode(gzip.compress(b'x'*1000)).decode())


@pytest.mark.parametrize('status',['137','656'])
def test_distribution_cooldown(status):
    with pytest.raises(fiscal.RecoveryError) as error:
        fiscal.distribution_result(envelope('retDistDFeInt',{'cStat':status,'xMotivo':'Pausa'}),key('55'))
    assert error.value.cooldown


def test_sp_recover_and_cancelled_status():
    note,protocol = note_and_protocol()
    sae = etree.Element('{%s}proc' % fiscal.NS)
    wrapper = etree.SubElement(sae,'{%s}nfeProc' % fiscal.NS)
    etree.SubElement(wrapper,'{%s}nProt' % fiscal.NS).text = '135260000000001'
    wrapper.append(note)
    class Fake:
        def query(self,endpoint,operation,message,version,uf):
            if endpoint == fiscal.SP_STATUS:
                assert fiscal.field(message,'chNFe') == key()
                return envelope('retConsSitNFe',{'cStat':'101','xMotivo':'Cancelada'},[protocol])
            assert endpoint == fiscal.SP_DOWNLOAD
            return envelope('retNfceDownloadXML',{'cStat':'200'},[sae])
    output,code,reason = fiscal.recover(Fake(),key(),'nfce-sp','12345678000195','SP')
    assert code == '101' and 'CANCELADA' in reason
    assert fiscal.parse_xml(output).tag.endswith('nfeProc')
    output,_,_ = fiscal.recover(Fake(),key(),'nfce-sp','12345678000195','SP',True)
    assert output is None


def test_national_uses_certificate_uf_not_issuer_uf():
    class Fake:
        def query(self,endpoint,operation,message,version,uf):
            assert endpoint == fiscal.NATIONAL
            assert fiscal.field(message,'cUFAutor') == '13'
            assert fiscal.field(message,'CNPJ') == '12345678000195'
            assert message.findtext('{%s}consChNFe/{%s}chNFe' % (fiscal.NS,fiscal.NS)) == key('55')
            return envelope('retDistDFeInt',{'cStat':'137'})
    with pytest.raises(fiscal.RecoveryError):
        fiscal.recover(Fake(),key('55'),'nfe-national','12345678000195','AM')


@pytest.fixture(scope='module')
def a1():
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization.pkcs12 import serialize_key_and_certificates
    from cryptography.x509.oid import NameOID,ObjectIdentifier
    private = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'SYNTHETIC TEST')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(private.public_key())
            .serial_number(1).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.OtherName(ObjectIdentifier('2.16.76.1.3.3'),b'\x0c\x0e12345678000195')]),critical=False)
            .sign(private,hashes.SHA256()))
    return serialize_key_and_certificates(b'test',private,cert,None,serialization.BestAvailableEncryption(b'test-password'))


def test_a1_extracts_cnpj_and_rejects_wrong_password(a1):
    assert fiscal.certificate_cnpj(a1,'test-password') == '12345678000195'
    with pytest.raises(fiscal.RecoveryError):
        fiscal.certificate_cnpj(a1,'wrong')


def test_transport_blocks_arbitrary_destinations(a1):
    client = fiscal.FiscalClient(a1,'test-password')
    try:
        for url in ['http://nfce.fazenda.sp.gov.br/','https://example.com/','https://nfce.fazenda.sp.gov.br:8443/']:
            with pytest.raises(fiscal.RecoveryError):
                client.session.get(url)
    finally:
        client.close()


def test_client_loads_system_and_requests_trust_without_trusting_upload(a1,monkeypatch):
    import ssl
    from requests.certs import where
    from unittest.mock import Mock
    import requests_pkcs12
    context = Mock()
    adapter = Mock(ssl_context=context)
    monkeypatch.setattr(requests_pkcs12,'Pkcs12Adapter',lambda **kwargs:adapter)
    client = fiscal.FiscalClient(a1,'test-password')
    try:
        context.load_default_certs.assert_called_once_with(ssl.Purpose.SERVER_AUTH)
        context.load_verify_locations.assert_called_once_with(cafile=where())
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is True
    finally:
        client.close()


def test_actual_client_context_requires_hostname_and_trusted_server(a1):
    import ssl
    client = fiscal.FiscalClient(a1,'test-password')
    try:
        context = client.session.adapters['https://'].ssl_context
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is True
        assert context.cert_store_stats()['x509_ca'] > 0
    finally:
        client.close()


def test_official_sp_bundle_is_pinned_and_signatures_verify():
    import ssl
    from unittest.mock import Mock
    context = Mock()
    fiscal.load_sp_server_trust(context)
    assert context.load_verify_locations.call_count == 1
    pem = context.load_verify_locations.call_args.kwargs['cadata']
    assert pem.count('-----BEGIN CERTIFICATE-----') == 4
    assert 'PRIVATE KEY' not in pem
    real = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    fiscal.load_sp_server_trust(real)
    assert real.cert_store_stats()['x509_ca'] == 4
    assert real.verify_mode == ssl.CERT_REQUIRED and real.check_hostname


def test_sp_public_ca_only_applies_to_sp_adapter(a1):
    import ssl
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    pin = bytes.fromhex('6e0bff069a26994c15de2c4888cc54af84882e5495b7fbf66be9ccffec7489f6')
    client = fiscal.FiscalClient(a1,'test-password','nfce-sp')
    try:
        adapter = client.session.get_adapter(fiscal.SP_STATUS)
        assert adapter is not client.session.get_adapter(fiscal.NATIONAL)
        assert adapter.ssl_context.verify_mode == ssl.CERT_REQUIRED and adapter.ssl_context.check_hostname
        import hashlib
        assert pin in {hashlib.sha256(data).digest() for data in adapter.ssl_context.get_ca_certs(binary_form=True)}
    finally:
        client.close()


def test_tampered_public_ca_bundle_rejected(monkeypatch):
    from unittest.mock import Mock
    from pathlib import Path
    original = Path.read_bytes
    def replaced(path):
        data = original(path)
        if path.name == 'sefaz-sp-ca.pem':
            # Missing a pinned certificate is rejected before it enters SSL trust.
            return data[:data.index(b'-----END CERTIFICATE-----')+len(b'-----END CERTIFICATE-----')]
        return data
    monkeypatch.setattr(Path,'read_bytes',replaced)
    context = Mock()
    with pytest.raises(fiscal.RecoveryError) as error:
        fiscal.load_sp_server_trust(context)
    assert error.value.code == 'ca_bundle'
    context.load_verify_locations.assert_not_called()


@pytest.mark.parametrize('uf', fiscal.STATUS_UFS)
def test_state_status_and_complete_use_key_authorizer(uf):
    k = key('65', fiscal.UF_CODES[uf])
    note, protocol = note_and_protocol(k)
    calls = []
    class Fake:
        def query(self, endpoint, operation, msg, version, code):
            calls.append(endpoint)
            assert endpoint == fiscal.NFCE_STATUS[k[:2]] and code == k[:2]
            return envelope('retConsSitNFe', {'cStat':'100','xMotivo':'Autorizada'}, [protocol])
    provider = fiscal.key_validate(k)[1]
    assert fiscal.recover(Fake(), k, provider, k[6:20], 'SP', True)[0] is None
    output = fiscal.recover(Fake(), k, provider, k[6:20], 'SP', original=note)[0]
    assert fiscal.parse_xml(output)[0].find('{%s}infNFe' % fiscal.NS).get('Id') == 'NFe' + k
    assert len(calls) == 2


def test_other_state_download_rejected_without_network():
    class Fake:
        def query(self, *args):
            pytest.fail('Unexpected network')
    with pytest.raises(fiscal.RecoveryError):
        fiscal.recover(Fake(), key('65','29'), 'nfce-state', '12345678000195', 'SP')
