import base64
from email import message_from_bytes
import pytest
from services import email_access
from services.gmail_sender import send_message


@pytest.fixture
def gmail(monkeypatch):
    for key,value in {'EMAIL_PROVIDER':'gmail','EMAIL_FROM':'OmniXML <omnixml@gmail.com>',
        'AUTH_SECRET':'x'*32,'ALLOWED_EMAILS':'admin@example.com','GMAIL_CLIENT_ID':'synthetic-client',
        'GMAIL_CLIENT_SECRET':'synthetic-secret','GMAIL_REFRESH_TOKEN':'synthetic-refresh'}.items():
        monkeypatch.setenv('OMNIXML_'+key,value)


def test_gmail_send_mime_and_refresh(gmail,monkeypatch):
    calls=[]
    class Response:
        status_code=200
        def json(self): return {'access_token':'synthetic-access'}
    def post(url,**kwargs):
        calls.append((url,kwargs))
        return Response()
    monkeypatch.setattr('services.gmail_sender.requests.post',post)
    assert email_access.configured()
    email_access.send_code('admin@example.com','123456')
    assert len(calls)==2
    assert calls[0][0]=='https://oauth2.googleapis.com/token'
    assert calls[0][1]['data']['grant_type']=='refresh_token'
    assert calls[0][1]['data']['refresh_token']=='synthetic-refresh'
    assert calls[1][0]=='https://gmail.googleapis.com/gmail/v1/users/me/messages/send'
    assert calls[1][1]['headers']['Authorization']=='Bearer synthetic-access'
    message=message_from_bytes(base64.urlsafe_b64decode(calls[1][1]['json']['raw']))
    assert message['From']=='OmniXML <omnixml@gmail.com>'
    assert message['To']=='admin@example.com'
    assert b'123456' in message.get_payload(decode=True)
    for _,options in calls:
        assert options['allow_redirects'] is False and options['timeout']==15


@pytest.mark.parametrize('statuses,token', [([400], 'token'), ([302], 'token'), ([200], None), ([200,403], 'token'), ([200,302], 'token')])
def test_failures_do_not_expose_credentials(gmail,monkeypatch,statuses,token):
    class Response:
        def __init__(self,status): self.status_code=status
        def json(self): return {'access_token':token,'error_description':'synthetic-secret'}
    responses=iter(statuses)
    monkeypatch.setattr('services.gmail_sender.requests.post',lambda *a,**k:Response(next(responses)))
    from email.message import EmailMessage
    with pytest.raises(RuntimeError) as error:
        send_message(EmailMessage())
    assert 'synthetic' not in str(error.value)


def test_gmail_missing_credentials(gmail,monkeypatch):
    monkeypatch.delenv('OMNIXML_GMAIL_REFRESH_TOKEN')
    assert not email_access.configured()


@pytest.mark.parametrize('stage,payload,expected',[
    ('oauth_refresh',{'error':'invalid_grant','error_description':'SECRET private@example.com'},'invalid_grant'),
    ('oauth_refresh',{'error':'SECRET'},'provider_error'),
    ('gmail_send',{'error':{'message':'SECRET','errors':[{'reason':'insufficientPermissions'}]}},'insufficientPermissions'),
    ('gmail_send',{'error':{'errors':[{'reason':'SECRET'}]}},'provider_error'),
])
def test_diagnostics_allowlist(gmail,monkeypatch,caplog,stage,payload,expected):
    from email.message import EmailMessage
    class Response:
        status_code=400
        def json(self): return payload
    class Token:
        status_code=200
        def json(self): return {'access_token':'SECRET'}
    responses=iter([Response()] if stage=='oauth_refresh' else [Token(),Response()])
    monkeypatch.setattr('services.gmail_sender.requests.post',lambda *a,**k:next(responses))
    with pytest.raises(RuntimeError): send_message(EmailMessage())
    assert f'stage={stage} reason={expected} http_status=400' in caplog.text
    assert 'SECRET' not in caplog.text and 'private@example.com' not in caplog.text


def test_diagnostics_timeout_does_not_log_exception(gmail,monkeypatch,caplog):
    import requests
    from email.message import EmailMessage
    def timeout(*a,**k): raise requests.Timeout('SECRET refresh-token')
    monkeypatch.setattr('services.gmail_sender.requests.post',timeout)
    with pytest.raises(RuntimeError): send_message(EmailMessage())
    assert 'reason=timeout' in caplog.text and 'SECRET' not in caplog.text
