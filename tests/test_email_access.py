"""Password authentication, migration, revocation and CAPTCHA security."""
import secrets
import sqlite3
import pytest
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from web_app_browser import app
from services import email_access as auth, password_store as passwords

PASSWORD = 'Uma frase privada para testes 42!'


@pytest.fixture
def client(tmp_path, monkeypatch):
    for key in ('D1_ACCOUNT_ID','D1_DATABASE_ID','D1_API_TOKEN','CLIENTS_DATABASE_URL','ADMIN_EMAILS','RECAPTCHA_SITE_KEY','RECAPTCHA_SECRET_KEY','ADMIN_INITIAL_PASSWORD'):
        monkeypatch.delenv('OMNIXML_'+key, raising=False)
    for name, value in {'AUTH_SECRET':'test-secret-32-characters-minimum!', 'ALLOWED_EMAILS':'admin@example.com',
                        'EMAIL_FROM':'OmniXML <sender@example.com>', 'AUTH_DB':str(tmp_path/'auth.db'),
                        'CLIENTS_DB':str(tmp_path/'clients.db')}.items():
        monkeypatch.setenv('OMNIXML_'+name, value)
    app.config['TESTING'] = True
    return app.test_client()


def post(client, route, data):
    return client.post('/api/access/'+route, json=data, base_url='https://localhost', headers={'Origin':'https://localhost'})


def seed(email, password=PASSWORD):
    with passwords.connection() as db:
        db.execute('INSERT INTO credentials (email,password_hash,version,invite_digest,invite_expires) VALUES (?,?,?,NULL,0) ON CONFLICT(email) DO UPDATE SET password_hash=excluded.password_hash,version=excluded.version',
                   (email,generate_password_hash(password),secrets.token_hex(16)))


def test_session_logout_and_no_email_dependency(client, monkeypatch):
    seed('admin@example.com')
    monkeypatch.setenv('OMNIXML_EMAIL_PROVIDER','gmail')
    monkeypatch.setattr(requests,'post',lambda *a,**k:pytest.fail('Login must not send mail'))
    response=post(client,'login',{'email':'ADMIN@example.com','password':PASSWORD})
    assert response.status_code==200
    assert all(flag in response.headers['Set-Cookie'] for flag in ('Secure','HttpOnly','SameSite=Strict'))
    assert client.get('/api/access/session',base_url='https://localhost').json['authenticated']
    assert post(client,'logout',{}).status_code==200
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']
    assert post(client,'code',{}).status_code in (401,404)
    assert post(client,'verify',{}).status_code in (401,404)


def test_password_errors_and_rates_do_not_disclose_accounts(client):
    seed('admin@example.com')
    for email in ('admin@example.com','unknown@example.com'):
        for _ in range(10):
            response=post(client,'login',{'email':email,'password':'wrong'})
            assert response.status_code==401 and response.json=={'error':'E-mail ou senha inválidos.'}
        assert post(client,'login',{'email':email,'password':PASSWORD}).status_code==429


def test_origin_expiry_and_revocation(client,monkeypatch):
    seed('admin@example.com')
    assert client.post('/api/access/login',json={'email':'admin@example.com','password':PASSWORD}).status_code==403
    assert client.post('/api/access/login',base_url='https://localhost',headers={'Origin':'https://evil.example'},json={}).status_code==403
    assert post(client,'login',{'email':'admin@example.com','password':PASSWORD}).status_code==200
    assert client.post('/api/sefaz/recover',base_url='https://localhost',headers={'Origin':'https://localhost'},data={}).status_code==400
    with auth.connection() as db:
        db.execute('UPDATE password_sessions SET expires=0')
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']
    post(client,'login',{'email':'admin@example.com','password':PASSWORD})
    monkeypatch.setenv('OMNIXML_ALLOWED_EMAILS','another@example.com')
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']


def test_bootstrap_once_and_hashes_only(client,monkeypatch):
    monkeypatch.setenv('OMNIXML_ADMIN_EMAILS','admin@example.com')
    monkeypatch.setenv('OMNIXML_ADMIN_INITIAL_PASSWORD',PASSWORD)
    assert post(client,'login',{'email':'admin@example.com','password':PASSWORD}).status_code==200
    row=passwords.credential('admin@example.com')
    assert row[0].startswith('scrypt:') and check_password_hash(row[0],PASSWORD)
    monkeypatch.setenv('OMNIXML_ADMIN_INITIAL_PASSWORD','A different initial private password')
    assert post(client,'login',{'email':'admin@example.com','password':PASSWORD}).status_code==200
    with passwords.connection() as db:
        assert all(PASSWORD not in str(r) for r in db.execute('SELECT * FROM credentials'))


def test_invitation_once_expiry_replace_and_session_reset(client):
    seed('admin@example.com')
    post(client,'login',{'email':'admin@example.com','password':PASSWORD})
    token,_=passwords.invite('admin@example.com')
    replacement,_=passwords.invite('admin@example.com')
    assert post(client,'activate',{'invite':token,'password':PASSWORD}).status_code==400
    new_password='Outra frase privada muito diferente 99!'
    assert post(client,'activate',{'invite':replacement,'password':new_password}).status_code==200
    assert post(client,'activate',{'invite':replacement,'password':new_password}).status_code==400
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']
    assert post(client,'login',{'email':'admin@example.com','password':PASSWORD}).status_code==401
    assert post(client,'login',{'email':'admin@example.com','password':new_password}).status_code==200
    expired,_=passwords.invite('admin@example.com')
    with passwords.connection() as db:
        db.execute('UPDATE credentials SET invite_expires=0')
    assert post(client,'activate',{'invite':expired,'password':PASSWORD}).status_code==400


def test_invalid_invite_cannot_change_password_and_no_plaintext(client):
    seed('admin@example.com')
    token,_=passwords.invite('admin@example.com')
    with passwords.connection() as db:
        row=db.execute('SELECT * FROM credentials').fetchone()
        assert token not in str(row) and PASSWORD not in str(row)
    assert post(client,'activate',{'invite':token,'password':'short'}).status_code==400
    assert post(client,'activate',{'invite':'invalid','password':PASSWORD}).status_code==400
    assert check_password_hash(passwords.credential('admin@example.com')[0],PASSWORD)


def test_old_email_sessions_do_not_grant_access(client,monkeypatch):
    with sqlite3.connect(__import__('os').environ['OMNIXML_AUTH_DB']) as db:
        db.execute('CREATE TABLE sessions (value TEXT PRIMARY KEY,email TEXT,expires INTEGER)')
        db.execute('INSERT INTO sessions VALUES (?,?,?)',(auth.digest('old-session'),'admin@example.com',9999999999))
    client.set_cookie(auth.COOKIE,'old-session',secure=True)
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']


@pytest.mark.parametrize('result,status',[({'success':False},200),({'success':True,'hostname':'evil.example'},200),
    ({'success':True,'hostname':'localhost','error-codes':['Over free quota.']},200),({'success':True,'hostname':'localhost'},302)])
def test_captcha_fails_closed(client,monkeypatch,result,status):
    seed('admin@example.com')
    monkeypatch.setenv('OMNIXML_RECAPTCHA_SITE_KEY','public-key')
    monkeypatch.setenv('OMNIXML_RECAPTCHA_SECRET_KEY','private-key')
    class Response:
        status_code=status
        def json(self):return result
    def verify(url,**kwargs):
        assert url=='https://www.google.com/recaptcha/api/siteverify'
        assert kwargs['allow_redirects'] is False and kwargs['timeout']==(5,10)
        assert kwargs['data']=={'secret':'private-key','response':'challenge'}
        return Response()
    monkeypatch.setattr(requests,'post',verify)
    assert post(client,'login',{'email':'admin@example.com','password':PASSWORD,'captcha':'challenge'}).status_code==400
    assert not client.get('/api/access/session',base_url='https://localhost').json['authenticated']


def test_captcha_success_partial_config_and_csp(client,monkeypatch):
    seed('admin@example.com')
    monkeypatch.setenv('OMNIXML_RECAPTCHA_SITE_KEY','public-key')
    assert post(client,'login',{'email':'admin@example.com','password':PASSWORD}).status_code==400
    monkeypatch.setenv('OMNIXML_RECAPTCHA_SECRET_KEY','private-key')
    class Response:
        status_code=200
        def json(self):return {'success':True,'hostname':'localhost'}
    monkeypatch.setattr(requests,'post',lambda *a,**k:Response())
    for path in ('/login','/activate'):
        response=client.get(path,base_url='https://localhost')
        assert 'data-sitekey="public-key"' in response.text
        assert 'https://www.google.com/recaptcha/' in response.headers['Content-Security-Policy']
        assert 'private-key' not in response.text
    assert "frame-src 'none'" in client.get('/privacy',base_url='https://localhost').headers['Content-Security-Policy']
    assert post(client,'login',{'email':'admin@example.com','password':PASSWORD,'captcha':'challenge'}).status_code==200


def test_configuration_payload_and_body_limits(client,monkeypatch):
    assert auth.configured()
    assert post(client,'login',[]).status_code==400
    assert post(client,'activate',[]).status_code==400
    assert post(client,'login',{'password':'x'*9000}).status_code==413
    monkeypatch.setenv('OMNIXML_AUTH_SECRET','short')
    assert not auth.configured()
    assert post(client,'login',{}).status_code==503


def test_invitation_consumption_is_atomic(client):
    from concurrent.futures import ThreadPoolExecutor
    seed('admin@example.com')
    token,_=passwords.invite('admin@example.com')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:passwords.activate(token,PASSWORD),range(2)))
    assert sorted(results)==[False,True]


def test_admin_invitation_and_client_complete_flow(client,monkeypatch):
    from services import client_registry
    monkeypatch.setenv('OMNIXML_ADMIN_EMAILS','admin@example.com')
    seed('admin@example.com')
    post(client,'login',{'email':'admin@example.com','password':PASSWORD})
    headers={'Origin':'https://localhost'}
    email='customer@example.com'
    assert client.post('/api/admin/clients',json={'email':email,'action':'add'},base_url='https://localhost',headers=headers).status_code==200
    result=client.post('/api/admin/password-invite',json={'email':email},base_url='https://localhost',headers=headers)
    assert result.status_code==200 and result.headers['Cache-Control']=='no-store'
    assert result.json['url'].startswith('https://localhost/activate#')
    customer=app.test_client()
    assert customer.post('/api/admin/password-invite',json={'email':email},base_url='https://localhost',headers=headers).status_code==401
    token=result.json['url'].split('#')[1]
    assert post(customer,'activate',{'invite':token,'password':PASSWORD}).status_code==200
    assert post(customer,'login',{'email':email,'password':PASSWORD}).status_code==200
    assert customer.get('/',base_url='https://localhost').status_code==200
    assert customer.post('/api/admin/password-invite',json={'email':email},base_url='https://localhost',headers=headers).status_code==403
    reset,_=passwords.invite(email)
    client_registry.change(email,'block');passwords.revoke(email)
    client_registry.change(email,'enable')
    assert post(customer,'activate',{'invite':reset,'password':PASSWORD}).status_code==400
    assert not customer.get('/api/access/session',base_url='https://localhost').json['authenticated']


def test_captcha_timeout_and_malformed_payload(client,monkeypatch):
    monkeypatch.setenv('OMNIXML_RECAPTCHA_SITE_KEY','public')
    monkeypatch.setenv('OMNIXML_RECAPTCHA_SECRET_KEY','secret')
    def timeout(*a,**k):raise requests.Timeout('secret')
    monkeypatch.setattr(requests,'post',timeout)
    response=post(client,'login',{'email':'admin@example.com','password':PASSWORD,'captcha':'challenge'})
    assert response.status_code==400 and 'secret' not in response.text
    class Response:
        status_code=200
        def json(self):return []
    monkeypatch.setattr(requests,'post',lambda *a,**k:Response())
    assert post(client,'login',{'email':'admin@example.com','password':PASSWORD,'captcha':'challenge'}).status_code==400
