import sqlite3
import pytest
import requests
from test_email_access import client
from test_client_admin import login, change
from services import client_registry, d1_registry
from web_app_browser import app


def configure(monkeypatch):
    monkeypatch.setenv('OMNIXML_ADMIN_EMAILS','admin@example.com')
    monkeypatch.setenv('OMNIXML_D1_ACCOUNT_ID','a'*32)
    monkeypatch.setenv('OMNIXML_D1_DATABASE_ID','11111111-1111-1111-1111-111111111111')
    monkeypatch.setenv('OMNIXML_D1_API_TOKEN','private-token')


class Response:
    status_code = 200
    def __init__(self,data): self.data=data
    def json(self): return self.data


def test_d1_lifecycle_and_bound_values(client,monkeypatch):
    configure(monkeypatch)
    db=sqlite3.connect(':memory:')
    db.row_factory=sqlite3.Row
    calls=[]
    def post(url,headers,json,timeout,allow_redirects):
        assert url.startswith('https://api.cloudflare.com/client/v4/accounts/')
        assert headers=={'Authorization':'Bearer private-token'}
        assert timeout==(5,20) and allow_redirects is False
        calls.append(json)
        cur=db.execute(json['sql'],json['params'])
        rows=[dict(row) for row in cur.fetchall()]
        return Response({'success':True,'result':[{'success':True,'results':rows,'meta':{'changes':max(0,cur.rowcount)}}]})
    monkeypatch.setattr(requests,'post',post)
    login(client,'admin@example.com',monkeypatch)
    email="o'connor@example.com"
    assert change(client,email,'add').status_code==200
    customer=app.test_client()
    login(customer,email,monkeypatch)
    rows=client.get('/api/admin/clients',base_url='https://localhost').json['clients']
    assert any(r['email']==email and r['active'] for r in rows)
    assert change(client,email,'block').status_code==200
    assert not customer.get('/api/access/session',base_url='https://localhost').json['authenticated']
    assert change(client,email,'enable').status_code==200
    assert client_registry.allowed(email)
    assert change(client,email,'delete').status_code==200
    assert not client_registry.allowed(email)
    assert all(email not in call['sql'] for call in calls)
    assert [r[1] for r in db.execute('PRAGMA table_info(clients)')]==['email','active','created']
    db.close()


@pytest.mark.parametrize('failure',['http','api','query','json','timeout'])
def test_d1_failures_are_closed_and_sanitized(client,monkeypatch,failure):
    monkeypatch.setenv('OMNIXML_ADMIN_EMAILS','admin@example.com')
    login(client,'admin@example.com',monkeypatch)
    configure(monkeypatch)
    def post(*args,**kwargs):
        if failure=='timeout': raise requests.Timeout('private-token')
        if failure=='json': raise ValueError('private-token')
        response=Response({'success':failure!='api','errors':[{'message':'private-token'}],
                           'result':[{'success':failure!='query'}]})
        if failure=='http': response.status_code=403
        return response
    monkeypatch.setattr(requests,'post',post)
    response=change(client,'customer@example.com','add')
    assert response.status_code==503
    assert 'private-token' not in response.get_data(as_text=True)
    assert response.headers['Cache-Control']=='no-store'
    with pytest.raises(d1_registry.StorageUnavailable):
        client_registry.allowed('customer@example.com')


def test_partial_d1_never_falls_back(client,tmp_path,monkeypatch):
    monkeypatch.setenv('OMNIXML_D1_ACCOUNT_ID','a'*32)
    monkeypatch.delenv('OMNIXML_D1_DATABASE_ID',raising=False)
    monkeypatch.delenv('OMNIXML_D1_API_TOKEN',raising=False)
    monkeypatch.setenv('OMNIXML_CLIENTS_DB',str(tmp_path/'fallback.db'))
    with pytest.raises(d1_registry.StorageUnavailable):
        client_registry.allowed('customer@example.com')
    assert not (tmp_path/'fallback.db').exists()
