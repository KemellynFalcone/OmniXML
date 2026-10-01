"""Optional authenticated download area, separate from browser-local auditing."""
import hmac
import io
import os
import ssl
import threading
import time
from collections import deque
from urllib.parse import quote, urlsplit

from flask import Blueprint, Request, Response, current_app, jsonify, render_template, request
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


def connection_diagnostic(error, stage):
    """Return fixed descriptions only; exception messages may contain secrets/SOAP."""
    from requests.exceptions import ConnectionError, HTTPError, SSLError, Timeout
    from zeep.exceptions import Error as ZeepError
    labels = {'a1_tls':'carregar o A1 na conexão TLS',
              'wsdl':'carregar o contrato WSDL da SEFAZ',
              'soap':'enviar a consulta SOAP à SEFAZ'}
    step = labels.get(stage,'processar a consulta fiscal')
    if isinstance(error, SSLError):
        if 'CERTIFICATE_VERIFY_FAILED' in str(error):
            code, message = 'tls_verify', 'O servidor não conseguiu validar a cadeia TLS do serviço da SEFAZ.'
            pending, seen, verification = [error], set(), None
            while pending and len(seen) < 30:
                item = pending.pop()
                if id(item) in seen:
                    continue
                seen.add(id(item))
                if isinstance(item, ssl.SSLCertVerificationError):
                    verification = getattr(item,'verify_code',None)
                    break
                pending.extend(value for value in getattr(item,'args',()) if isinstance(value,BaseException))
                pending.extend(value for value in (getattr(item,'reason',None),getattr(item,'__cause__',None),getattr(item,'__context__',None)) if isinstance(value,BaseException))
            explanations = {2:'emissor não localizado',9:'certificado ainda não válido',10:'certificado expirado',18:'certificado autoassinado',19:'cadeia com certificado não confiável',20:'emissor não localizado na cadeia de confiança',21:'cadeia de confiança incompleta',62:'nome do servidor divergente'}
            if isinstance(verification,int) and 0 <= verification <= 999:
                message += ' Verificação TLS '+str(verification)+': '+explanations.get(verification,'falha de validação')+'.'
        else:
            code, message = 'tls_handshake', 'A negociação TLS com a SEFAZ falhou. O serviço pode ter recusado a conexão ou o certificado cliente.'
    elif isinstance(error, Timeout):
        code, message = 'timeout', 'A SEFAZ não respondeu dentro do tempo limite.'
    elif isinstance(error, HTTPError):
        status = error.response.status_code if error.response is not None else None
        suffix = str(status) if isinstance(status,int) and 100 <= status <= 599 else 'inesperado'
        code, message = 'http', 'O serviço da SEFAZ respondeu HTTP '+suffix+'.'
    elif isinstance(error, ConnectionError):
        code, message = 'network', 'O servidor não conseguiu estabelecer conexão com a SEFAZ (rede/DNS/conexão interrompida).'
    elif isinstance(error, ZeepError):
        code, message = 'soap_contract', 'Não foi possível interpretar o contrato ou a resposta SOAP da SEFAZ.'
    elif stage == 'a1_tls':
        code, message = 'a1_tls', 'O A1 foi aberto, mas não foi possível carregar sua chave e cadeia no contexto TLS.'
    else:
        code, message = 'internal', 'O processamento da consulta encontrou um erro interno.'
    return code, message+' Etapa: '+step+'.'


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
        except Exception as exc:
            stage = getattr(client,'stage','a1_tls') if client is not None else 'a1_tls'
            code, description = connection_diagnostic(exc,stage)
            current_app.logger.warning('sefaz_recovery_failure stage=%s category=%s',
                                       stage if stage in ('a1_tls','wsdl','soap') else 'unknown',code)
            return jsonify(error=description,code=code,stop_batch=True),502
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
