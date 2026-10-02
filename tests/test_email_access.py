import re
import pytest
from web_app_browser import app
from services import email_access as auth


@pytest.fixture
def client(tmp_path, monkeypatch):
    for name, value in {'AUTH_SECRET':'test-secret-32-characters-minimum!', 'ALLOWED_EMAILS':'admin@example.com', 'SMTP_HOST':'smtp.example.com', 'SMTP_USER':'user', 'SMTP_PASSWORD':'password', 'EMAIL_FROM':'OmniXML <sender@example.com>', 'EMAIL_PROVIDER':'resend', 'RESEND_API_KEY':'synthetic-key', 'AUTH_DB':str(tmp_path/'auth.db')}.items():
        monkeypatch.setenv('OMNIXML_'+name, value)
    app.config['TESTING'] = True
    return app.test_client()


def post(client, route, data):
    return client.post('/api/access/'+route, json=data, base_url='https://localhost', headers={'Origin':'https://localhost'})


def test_code_session_reuse_logout(client, monkeypatch):
    sent = []
    monkeypatch.setattr(auth, 'send_code', lambda email, code: sent.append((email,code)))
    assert post(client,'code',{'email':'ADMIN@example.com'}).status_code == 200
    assert re.fullmatch(r'\d{6}', sent[0][1])
    data = {'email':'admin@example.com','code':sent[0][1]}
    response = post(client,'verify',data)
    assert response.status_code == 200
    cookie = response.headers['Set-Cookie']
    assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=Strict' in cookie
    assert client.get('/api/access/session',base_url='https://localhost').json['authenticated']
    assert post(client,'verify',data).status_code == 400
    assert post(client,'logout',{}).status_code == 200
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']


def test_denied_email_not_sent(client, monkeypatch):
    monkeypatch.setattr(auth,'send_code',lambda *args: pytest.fail('unauthorized email'))
    assert post(client,'code',{'email':'other@example.com'}).status_code == 200
    assert post(client,'verify',{'email':'other@example.com','code':'123456'}).status_code == 400


def test_attempts_resend_expiry_and_origin(client,monkeypatch):
    sent=[]
    monkeypatch.setattr(auth,'send_code',lambda e,c:sent.append(c))
    post(client,'code',{'email':'admin@example.com'})
    assert post(client,'code',{'email':'admin@example.com'}).status_code == 429
    for _ in range(5):
        assert post(client,'verify',{'email':'admin@example.com','code':'invalid'}).status_code == 400
    assert post(client,'verify',{'email':'admin@example.com','code':sent[0]}).status_code == 400
    assert client.post('/api/access/code',json={'email':'admin@example.com'}).status_code == 503
    assert client.post('/api/access/code',base_url='https://localhost',headers={'Origin':'https://evil.example'},json={}).status_code == 503


def test_revocation_and_sefaz_session(client,monkeypatch):
    sent=[]
    monkeypatch.setattr(auth,'send_code',lambda e,c:sent.append(c))
    post(client,'code',{'email':'admin@example.com'})
    post(client,'verify',{'email':'admin@example.com','code':sent[0]})
    response=client.post('/api/sefaz/recover',base_url='https://localhost',headers={'Origin':'https://localhost'},data={})
    assert response.status_code == 400  # authentication passed; fiscal input invalid
    monkeypatch.setenv('OMNIXML_ALLOWED_EMAILS','another@example.com')
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']


def test_expired_code_and_session_and_smtp_failure(client,monkeypatch):
    sent=[]
    monkeypatch.setattr(auth,'send_code',lambda e,c:sent.append(c))
    post(client,'code',{'email':'admin@example.com'})
    with auth.connection() as db:
        db.execute('UPDATE codes SET expires=0')
    assert post(client,'verify',{'email':'admin@example.com','code':sent[0]}).status_code == 400
    with auth.connection() as db:
        db.execute('DELETE FROM rates')
    post(client,'code',{'email':'admin@example.com'})
    post(client,'verify',{'email':'admin@example.com','code':sent[-1]})
    with auth.connection() as db:
        db.execute('UPDATE sessions SET expires=0')
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']
    with auth.connection() as db:
        db.execute('DELETE FROM rates')
    def fail(*args):
        raise RuntimeError('secret SMTP password must not appear')
    monkeypatch.setattr(auth,'send_code',fail)
    response=post(client,'code',{'email':'admin@example.com'})
    assert response.status_code == 200 and b'secret SMTP' not in response.data
    with auth.connection() as db:
        assert not db.execute('SELECT * FROM codes').fetchall()


def test_https_email_transport(client,monkeypatch):
    import requests
    captured=[]
    class Response:
        status_code=200
    def send(url, **kwargs):
        captured.append((url,kwargs))
        return Response()
    monkeypatch.setattr(requests,'post',send)
    auth.send_code('admin@example.com','123456')
    url, options=captured[0]
    assert url == 'https://api.resend.com/emails'
    assert options['allow_redirects'] is False and options['timeout'] == 15
    assert options['json']['to'] == ['admin@example.com']
    assert '123456' in options['json']['text']
    Response.status_code=302
    with pytest.raises(RuntimeError):
        auth.send_code('admin@example.com','123456')


def test_configuration_and_invalid_payload(client,monkeypatch):
    assert auth.configured()
    assert post(client,'code',[]).status_code == 400
    assert post(client,'verify',[]).status_code == 400
    monkeypatch.setenv('OMNIXML_AUTH_SECRET','short')
    assert not auth.configured()
    assert post(client,'code',{'email':'admin@example.com'}).status_code == 503


def test_resend_cooldown_does_not_disclose_membership(client, monkeypatch):
    monkeypatch.setattr(auth, 'send_code', lambda *args: None)
    for email in ('admin@example.com', 'unknown@example.com'):
        assert post(client, 'code', {'email': email}).status_code == 200
        response = post(client, 'code', {'email': email})
        assert response.status_code == 429
        assert 1 <= int(response.headers['Retry-After']) <= 60
