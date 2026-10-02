from test_email_access import client, post
from services import email_access, client_registry, traffic_monitor
from web_app_browser import app


def login(client,email,monkeypatch):
    sent=[]
    monkeypatch.setattr(email_access,'send_code',lambda e,c:sent.append(c))
    assert post(client,'code',{'email':email}).status_code==200
    assert post(client,'verify',{'email':email,'code':sent[-1]}).status_code==200


def setup_registry(tmp_path,monkeypatch):
    monkeypatch.setenv('OMNIXML_ADMIN_EMAILS','admin@example.com')
    monkeypatch.setenv('OMNIXML_CLIENTS_DB',str(tmp_path/'clients.db'))


def change(client,email,action,origin='https://localhost'):
    return client.post('/api/admin/clients',json={'email':email,'action':action},base_url='https://localhost',headers={'Origin':origin})


def test_admin_client_lifecycle_and_revocation(client,tmp_path,monkeypatch):
    setup_registry(tmp_path,monkeypatch)
    login(client,'admin@example.com',monkeypatch)
    assert client.get('/admin',base_url='https://localhost').status_code==200
    assert change(client,'client@example.com','add').status_code==200
    with client_registry.connection() as db:
        assert [r[1] for r in db.execute('PRAGMA table_info(clients)')]==['email','active','created']
    customer=app.test_client()
    login(customer,'client@example.com',monkeypatch)
    assert customer.get('/api/admin/clients',base_url='https://localhost').status_code==403
    assert customer.get('/api/admin/traffic',base_url='https://localhost').status_code==403
    assert customer.get('/admin',base_url='https://localhost').status_code==403
    assert change(customer,'intruder@example.com','add').status_code==403
    assert change(client,'client@example.com','block').status_code==200
    assert not customer.get('/api/access/session',base_url='https://localhost').json['authenticated']
    assert not client_registry.allowed('client@example.com')
    assert change(client,'client@example.com','enable').status_code==200
    # Old session stays invalid even after re-enabling.
    assert not customer.get('/api/access/session',base_url='https://localhost').json['authenticated']
    assert change(client,'client@example.com','delete').status_code==200
    assert not client_registry.allowed('client@example.com')
    with client_registry.connection() as db:
        assert not db.execute('SELECT * FROM clients').fetchall()


def test_admin_origin_bootstrap_and_storage_guard(client,tmp_path,monkeypatch):
    setup_registry(tmp_path,monkeypatch)
    login(client,'admin@example.com',monkeypatch)
    assert change(client,'client@example.com','add','https://evil.example').status_code==403
    assert change(client,'admin@example.com','delete').status_code==400
    assert change(client,'bad','add').status_code==400
    monkeypatch.delenv('OMNIXML_CLIENTS_DB')
    assert change(client,'client@example.com','add').status_code==503
    assert not client.get('/api/admin/clients',base_url='https://localhost').json['editable']


def test_registry_survives_connection_recreation(client,tmp_path,monkeypatch):
    setup_registry(tmp_path,monkeypatch)
    client_registry.change('client@example.com','add')
    assert client_registry.allowed('client@example.com')
    assert any(r['email']=='client@example.com' for r in client_registry.list_clients())


def test_login_privacy_and_private_counters(client,tmp_path,monkeypatch):
    setup_registry(tmp_path,monkeypatch)
    assert client.get('/admin',base_url='https://localhost').status_code==302
    assert client.get('/login',base_url='https://localhost').status_code==200
    assert client.get('/privacy',base_url='https://localhost').status_code==200
    assert client.get('/api/admin/traffic',base_url='https://localhost').status_code==403
    login(client,'admin@example.com',monkeypatch)
    assert client.get('/login',base_url='https://localhost').status_code==302
    before=traffic_monitor.snapshot()
    client.get('/privacy',base_url='https://localhost')
    after=traffic_monitor.snapshot()
    assert after['requests']==before['requests']+1 and after['active']==0
    response=client.get('/api/admin/traffic',base_url='https://localhost')
    assert response.status_code==200 and response.headers['Cache-Control']=='no-store'
    assert traffic_monitor.snapshot()['requests']==after['requests']
    assert set(response.json)=={'requests','active','success','rejected','errors','bytes_in','bytes_out','fiscal','access','pages','average_ms','uptime_seconds','worker'}
    assert 'admin@example.com' not in response.get_data(as_text=True)
