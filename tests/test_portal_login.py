from test_email_access import client, post
from test_client_admin import login


def test_global_gate_and_single_session(client,monkeypatch):
    monkeypatch.setenv('OMNIXML_SEFAZ_TOKEN','legacy-token')
    for path in ('/','/downloads','/admin'):
        response=client.get(path,base_url='https://localhost')
        assert response.status_code==302 and response.headers['Location']=='/login'
    assert client.get('/api/sefaz/capabilities',base_url='https://localhost',headers={'Authorization':'Bearer legacy-token'}).status_code==401
    for path in ('/login','/privacy','/health','/api/access/session','/static/access.js'):
        assert client.get(path,base_url='https://localhost').status_code==200
    login(client,'admin@example.com',monkeypatch)
    for path in ('/','/downloads','/api/sefaz/capabilities'):
        assert client.get(path,base_url='https://localhost').status_code==200
    assert client.get('/login',base_url='https://localhost').headers['Location']=='/'
    assert client.get('/admin',base_url='https://localhost').status_code==403
    assert post(client,'logout',{}).status_code==200
    assert client.get('/',base_url='https://localhost').status_code==302
