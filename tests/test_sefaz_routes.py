import io

import pytest

import web_app_browser
from services import sefaz_routes as routes
from services.sefaz_download import RecoveryError
from test_sefaz_download import a1, key, note_and_protocol


@pytest.fixture
def browser(monkeypatch):
    monkeypatch.delenv('OMNIXML_SEFAZ_TOKEN',raising=False)
    routes._history.clear(); routes._cooldowns.clear()
    return web_app_browser.app.test_client()


def post(browser,a1,k=None,**options):
    return browser.post('/api/sefaz/recover',data={'certificate':(io.BytesIO(a1),'synthetic.pfx'),
                        'password':'test-password','key':k or key(),'uf':'SP'},
                        headers=options.pop('headers',{'Origin':'http://localhost'}),**options)


def test_page_and_unchanged_audit(browser):
    assert browser.get('/downloads').status_code == 200
    assert b'/downloads' in browser.get('/').data
    health = browser.get('/health').json
    assert health['processing'] == 'browser-local' and health['xml_upload'] is False


@pytest.mark.parametrize('origin',['https://evil.example','http://localhost:9999','null',''])
def test_origin_required(browser,a1,origin):
    assert post(browser,a1,headers={'Origin':origin}).status_code == 403


def test_remote_requires_token_and_https(browser,a1,monkeypatch):
    options = {'base_url':'https://example.com','environ_overrides':{'REMOTE_ADDR':'203.0.113.2'}}
    assert post(browser,a1,headers={'Origin':'https://example.com'},**options).status_code == 403
    monkeypatch.setenv('OMNIXML_SEFAZ_TOKEN','test-token')
    assert post(browser,a1,headers={'Origin':'https://example.com','Authorization':'Bearer wrong'},**options).status_code == 403
    assert post(browser,a1,base_url='http://example.com',environ_overrides={'REMOTE_ADDR':'203.0.113.2'},headers={'Origin':'http://example.com','Authorization':'Bearer test-token'}).status_code == 403


def test_forwarded_ip_cannot_enable_local_access(browser,a1):
    assert post(browser,a1,environ_overrides={'REMOTE_ADDR':'203.0.113.2'},headers={'Origin':'http://localhost','X-Forwarded-For':'127.0.0.1'}).status_code == 403


def test_success_final_attachment_no_cache(browser,a1,monkeypatch):
    from services.sefaz_download import processed
    xml = processed(*note_and_protocol(),key())
    class Fake:
        closed = False
        def __init__(self,*args): pass
        def close(self): Fake.closed = True
    monkeypatch.setattr(routes,'FiscalClient',Fake)
    monkeypatch.setattr(routes,'recover',lambda *args:(xml,'100','Autorizada'))
    response = post(browser,a1)
    assert response.status_code == 200 and response.data == xml
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-SEFAZ-cStat'] == '100'
    assert response.headers['Content-Disposition'].endswith(key()+'-procNFe.xml"')
    assert Fake.closed


def test_remote_token_success(browser,a1,monkeypatch):
    monkeypatch.setenv('OMNIXML_SEFAZ_TOKEN','test-token')
    monkeypatch.setattr(routes,'FiscalClient',lambda *args:None)
    monkeypatch.setattr(routes,'recover',lambda *args:(None,'100','Autorizada'))
    assert post(browser,a1,base_url='https://example.com',environ_overrides={'REMOTE_ADDR':'203.0.113.2'},
                headers={'Origin':'https://example.com','Authorization':'Bearer test-token'}).status_code == 200


def test_certificate_size_limit(browser):
    response = browser.post('/api/sefaz/recover',headers={'Origin':'http://localhost'},data={
        'certificate':(io.BytesIO(b'x'*(2*1024*1024+1)),'synthetic.pfx'),'key':key(),'uf':'SP'})
    assert response.status_code == 400


def test_total_size_limit(browser):
    response = browser.post('/api/sefaz/recover',headers={'Origin':'http://localhost'},data={
        'certificate':(io.BytesIO(b'x'*(3*1024*1024+1)),'synthetic.pfx'),'key':key(),'uf':'SP'})
    assert response.status_code == 413


def test_unsupported_before_certificate_or_network(browser):
    response = browser.post('/api/sefaz/recover',headers={'Origin':'http://localhost'},data={'key':key('65','33'),'uf':'RJ'})
    assert response.status_code == 400 and response.json['code'] == 'unsupported'


def test_cooldown_stops_next_request(browser,a1,monkeypatch):
    monkeypatch.setattr(routes,'FiscalClient',lambda *args:None)
    def error(*args): raise RecoveryError('Consumo indevido','656',True)
    monkeypatch.setattr(routes,'recover',error)
    response = post(browser,a1,key('55'))
    assert response.status_code == 422 and response.json['stop_batch']
    assert post(browser,a1,key('55')).status_code == 429


def test_exception_does_not_expose_secrets(browser,a1,monkeypatch):
    def error(*args): raise RuntimeError('SECRET password SOAP private_key')
    monkeypatch.setattr(routes,'FiscalClient',error)
    response = post(browser,a1)
    assert response.status_code == 502 and b'SECRET' not in response.data


def test_busy_request_does_not_call_sefaz(browser,a1):
    routes._active.acquire()
    try: assert post(browser,a1).status_code == 429
    finally: routes._active.release()


def test_a1_upload_stream_stays_in_memory(browser):
    from services.sefaz_routes import FiscalRequest
    request = FiscalRequest.from_values(path='/api/sefaz/recover',method='POST',data={
        'certificate':(io.BytesIO(b'x'*(700*1024)),'synthetic.pfx')})
    try:
        assert isinstance(request.files['certificate'].stream,io.BytesIO)
    finally:
        request.close()
