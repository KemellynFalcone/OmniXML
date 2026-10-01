"""Optional authenticated download area, separate from browser-local auditing."""
import hmac
import io
import os
import threading
import time
from collections import deque
from urllib.parse import quote, urlsplit

from flask import Blueprint, Request, Response, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from services.sefaz_download import (FiscalClient, RecoveryError, UF_CODES, certificate_cnpj,
                                    key_validate, recover)

class FiscalRequest(Request):
    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):
        if self.path == '/api/sefaz/recover':
            return io.BytesIO()
        return super()._get_file_stream(total_content_length,content_type,filename,content_length)


blueprint = Blueprint('sefaz',__name__)
_active = threading.Lock()
_history = {}
_cooldowns = {}


def access_allowed():
    token = os.environ.get('OMNIXML_SEFAZ_TOKEN','')
    local = request.remote_addr in ('127.0.0.1','::1') and request.host.split(':')[0] in ('localhost','127.0.0.1')
    if not local and not request.is_secure:
        return False
    origin = request.headers.get('Origin')
    if not origin or urlsplit(origin).netloc != request.host or urlsplit(origin).scheme != request.scheme:
        return False
    if token:
        return hmac.compare_digest(request.headers.get('Authorization','').encode(),('Bearer '+token).encode())
    return local


@blueprint.get('/downloads')
def downloads():
    return render_template('downloads.html',ufs=UF_CODES)


@blueprint.get('/api/sefaz/capabilities')
def capabilities():
    return jsonify(nfe='Distribuição nacional: todas as UFs, conforme permissão do certificado.',
                   nfce='Download e situação: SP (SAE). Outras UFs ainda não implementadas.',
                   other='CT-e, MDF-e e outros modelos ainda não implementados.',
                   enabled=bool(os.environ.get('OMNIXML_SEFAZ_TOKEN')) or
                           (request.remote_addr in ('127.0.0.1','::1') and request.host.split(':')[0] in ('localhost','127.0.0.1')))


@blueprint.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


@blueprint.post('/api/sefaz/recover')
def download_xml():
    if not access_allowed():
        return jsonify(error='Recuperação protegida. Configure o token do servidor e use HTTPS; localmente, acesse por localhost.',code='access'),403
    request.max_content_length = 3 * 1024 * 1024
    try:
        key, provider = key_validate(request.form.get('key',''))
        uf = request.form.get('uf','').upper()
        action = request.form.get('action','download')
        if uf not in UF_CODES or action not in ('download','status'):
            raise RecoveryError('UF do titular ou ação inválida.')
        if provider == 'nfe-national' and action == 'status':
            raise RecoveryError('Consulta de situação disponível nesta versão para NFC-e/SP.', 'unsupported')
        upload = request.files.get('certificate')
        if upload is None:
            raise RecoveryError('Selecione o certificado A1 (.pfx/.p12).')
        data = upload.read(2 * 1024 * 1024 + 1)
        if not data or len(data) > 2 * 1024 * 1024:
            raise RecoveryError('A1 vazio ou maior que 2 MB.')
        password = request.form.get('password','')
        if len(password) > 1024:
            raise RecoveryError('Senha excede o limite permitido.')
        cnpj = certificate_cnpj(data,password)
        if provider == 'nfce-sp' and cnpj != key[6:20]:
            raise RecoveryError('O SAE de SP exige o certificado do emitente da NFC-e.')
    except RequestEntityTooLarge:
        return jsonify(error='Envio excede 3 MB.',code='size'),413
    except RecoveryError as exc:
        return jsonify(error=str(exc),code=exc.code),400
    if not _active.acquire(blocking=False):
        return jsonify(error='Outra consulta está em andamento. Aguarde e tente novamente.',code='busy'),429
    try:
        now = time.monotonic()
        identity = (cnpj,provider)
        for old in list(_history):
            if not _history[old] or now - _history[old][-1] > 3600:
                _history.pop(old,None)
                _cooldowns.pop(old,None)
        if len(_history) >= 1000 and identity not in _history:
            return jsonify(error='Limite temporário do servidor atingido.',code='limit'),429
        history = _history.setdefault(identity,deque())
        while history and now-history[0] >= 3600:
            history.popleft()
        limit = 20 if provider == 'nfe-national' else 120
        if now < _cooldowns.get(identity,0) or len(history) >= limit:
            return jsonify(error='Pausa de segurança ativa para este CNPJ/serviço. Aguarde uma hora antes de novas consultas.',code='cooldown'),429
        history.append(now)
        client = None
        try:
            client = FiscalClient(data,password)
            xml, code, reason = recover(client,key,provider,cnpj,uf,action == 'status')
        except RecoveryError as exc:
            if exc.cooldown:
                _cooldowns[identity] = time.monotonic()+3600
            return jsonify(error=str(exc),code=exc.code,stop_batch=exc.cooldown),422
        except Exception:
            # Do not expose exception traces, SOAP envelopes, certificate paths or secrets.
            return jsonify(error='Falha na conexão segura com a SEFAZ. Verifique a disponibilidade do serviço e a cadeia do certificado.',code='connection'),502
        finally:
            if client is not None:
                client.close()
        if xml is None:
            return jsonify(key=key,cStat=code,xMotivo=reason)
        return Response(xml,mimetype='application/xml',headers={
            'Content-Disposition':'attachment; filename="'+key+'-procNFe.xml"',
            'X-SEFAZ-cStat':code,'X-SEFAZ-Motivo':quote(reason,safe=''),
        })
    finally:
        _active.release()
