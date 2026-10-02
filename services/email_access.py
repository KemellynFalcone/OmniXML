"""Short-lived email codes and opaque, revocable sessions shared by workers."""
import hashlib
import hmac
import os
import re
import secrets
import smtplib
import sqlite3
import time
from email.message import EmailMessage
from contextlib import contextmanager

from flask import Blueprint, current_app, jsonify, request

blueprint = Blueprint('email_access', __name__)
COOKIE = 'omnixml_access'


def configured():
    common = len(os.environ.get('OMNIXML_AUTH_SECRET', '')) >= 32 and all(
        os.environ.get(k) for k in ('OMNIXML_ALLOWED_EMAILS', 'OMNIXML_EMAIL_FROM'))
    provider = os.environ.get('OMNIXML_EMAIL_PROVIDER', 'resend')
    if provider == 'gmail':
        return common and all(os.environ.get(k) for k in
            ('OMNIXML_GMAIL_CLIENT_ID', 'OMNIXML_GMAIL_CLIENT_SECRET', 'OMNIXML_GMAIL_REFRESH_TOKEN'))
    if provider == 'resend':
        return common and bool(os.environ.get('OMNIXML_RESEND_API_KEY'))
    return common and provider == 'smtp' and all(os.environ.get(k) for k in
        ('OMNIXML_SMTP_HOST', 'OMNIXML_SMTP_USER', 'OMNIXML_SMTP_PASSWORD'))


def allowed(email):
    from services.client_registry import allowed as client_allowed
    return client_allowed(email)


def digest(value):
    return hmac.new(os.environ.get('OMNIXML_AUTH_SECRET', '').encode(), value.encode(), hashlib.sha256).hexdigest()


@contextmanager
def connection():
    db = sqlite3.connect(os.environ.get('OMNIXML_AUTH_DB', '/tmp/omnixml-auth.sqlite3'), timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS codes (email TEXT PRIMARY KEY, value TEXT, expires INTEGER, attempts INTEGER, sent INTEGER)')
    db.execute('CREATE TABLE IF NOT EXISTS sessions (value TEXT PRIMARY KEY, email TEXT, expires INTEGER)')
    db.execute('CREATE TABLE IF NOT EXISTS rates (value TEXT PRIMARY KEY, start INTEGER, count INTEGER)')
    try:
        with db:
            now = int(time.time())
            db.execute('DELETE FROM codes WHERE expires<=?', (now,))
            db.execute('DELETE FROM sessions WHERE expires<=?', (now,))
            db.execute('DELETE FROM rates WHERE start<?', (now-3600,))
        with db:
            yield db
    finally:
        db.close()


def secure_origin():
    from urllib.parse import urlsplit
    origin = urlsplit(request.headers.get('Origin', ''))
    return request.is_secure and origin.scheme == request.scheme and origin.netloc == request.host


def identity():
    if not configured():
        return None
    token = request.cookies.get(COOKIE, '')
    if len(token) > 128 or not token:
        return None
    with connection() as db:
        row = db.execute('SELECT email FROM sessions WHERE value=? AND expires>?', (digest(token), int(time.time()))).fetchone()
    return row[0] if row and allowed(row[0]) else None


def send_code(email, code):
    if os.environ.get('OMNIXML_EMAIL_PROVIDER', 'resend') == 'resend':
        import requests
        response = requests.post('https://api.resend.com/emails',
            headers={'Authorization':'Bearer '+os.environ['OMNIXML_RESEND_API_KEY']},
            json={'from':os.environ['OMNIXML_EMAIL_FROM'], 'to':[email],
                  'subject':'Seu código de acesso ao OmniXML',
                  'text':f'Seu código de acesso é: {code}\nVálido por 10 minutos e para um único uso. Se não solicitou, ignore este e-mail. Não compartilhe o código.'},
            timeout=15, allow_redirects=False)
        if response.status_code not in (200, 201):
            raise RuntimeError('email provider rejected request')
        return
    message = EmailMessage()
    message['From'] = os.environ['OMNIXML_EMAIL_FROM']
    message['To'] = email
    message['Subject'] = 'Seu código de acesso ao OmniXML'
    message.set_content(f'Seu código de acesso é: {code}\n\nVálido por 10 minutos e para um único uso. Se não solicitou, ignore este e-mail. Não compartilhe o código.')
    if os.environ.get('OMNIXML_EMAIL_PROVIDER', 'resend') == 'gmail':
        from services.gmail_sender import send_message
        send_message(message)
        return
    host = os.environ['OMNIXML_SMTP_HOST']
    port = int(os.environ.get('OMNIXML_SMTP_PORT', '587'))
    import ssl
    context = ssl.create_default_context()
    transport = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
    kwargs = {'context': context} if port == 465 else {}
    with transport(host, port, timeout=15, **kwargs) as smtp:
        if port != 465:
            smtp.starttls(context=context)
        smtp.login(os.environ['OMNIXML_SMTP_USER'], os.environ['OMNIXML_SMTP_PASSWORD'])
        smtp.send_message(message)


def rate_limit(db, bucket, limit):
    now = int(time.time())
    row = db.execute('SELECT start,count FROM rates WHERE value=?', (bucket,)).fetchone()
    if row and now - row[0] < 3600:
        if row[1] >= limit:
            return False
        db.execute('UPDATE rates SET count=count+1 WHERE value=?', (bucket,))
    else:
        db.execute('INSERT OR REPLACE INTO rates VALUES (?,?,1)', (bucket, now))
    return True


@blueprint.before_request
def limit_body():
    request.max_content_length = 4096


@blueprint.get('/api/access/session')
def session_state():
    email = identity()
    from services.client_registry import admins
    return jsonify(configured=configured(), authenticated=bool(email), email=email, admin=email in admins())


@blueprint.post('/api/access/code')
def request_code():
    if not configured() or not secure_origin():
        return jsonify(error='Acesso por e-mail indisponível. Contate o administrador.'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Requisição inválida.'), 400
    email = str(data.get('email', '')).strip().lower()
    if len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        return jsonify(error='Informe um e-mail válido.'), 400
    now = int(time.time())
    code = f'{secrets.randbelow(1000000):06d}'
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM sessions WHERE expires<=?', (now,))
        db.execute('DELETE FROM codes WHERE expires<=?', (now,))
        db.execute('DELETE FROM rates WHERE start<?', (now-3600,))
        ip = digest('ip:' + (request.remote_addr or 'unknown'))
        if not rate_limit(db, ip, 30) or not rate_limit(db, digest('email:'+email), 5):
            return jsonify(error='Limite de solicitações atingido. Aguarde antes de tentar novamente.'), 429
        row = db.execute('SELECT sent FROM codes WHERE email=?', (email,)).fetchone()
        if row and now-row[0] < 60:
            return jsonify(error='Aguarde um minuto antes de pedir outro código.'), 429
        if allowed(email):
            db.execute('INSERT OR REPLACE INTO codes VALUES (?,?,?,0,?)', (email, digest(email+':'+code), now+600, now))
    if allowed(email):
        try:
            send_code(email, code)
        except Exception:
            current_app.logger.warning('omnixml_email_delivery_failed; check email provider configuration')
            with connection() as db:
                db.execute('DELETE FROM codes WHERE email=? AND value=?', (email, digest(email+':'+code)))
            # Do not expose SMTP credentials or account membership.
    return jsonify(message='Se o e-mail estiver liberado, você receberá um código. Confira também o spam.')


@blueprint.post('/api/access/verify')
def verify_code():
    if not configured() or not secure_origin():
        return jsonify(error='Acesso por e-mail indisponível.'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Requisição inválida.'), 400
    email = str(data.get('email', '')).strip().lower()
    code = str(data.get('code', ''))
    now = int(time.time())
    token = secrets.token_urlsafe(32)
    success = False
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if not rate_limit(db, digest('verify:'+(request.remote_addr or 'unknown')), 60):
            return jsonify(error='Muitas tentativas. Aguarde antes de tentar novamente.'), 429
        row = db.execute('SELECT value,expires,attempts FROM codes WHERE email=?', (email,)).fetchone()
        if row and row[1] > now and row[2] < 5 and allowed(email):
            db.execute('UPDATE codes SET attempts=attempts+1 WHERE email=?', (email,))
            if re.fullmatch(r'[0-9]{6}', code) and hmac.compare_digest(row[0], digest(email+':'+code)):
                db.execute('DELETE FROM codes WHERE email=?', (email,))
                db.execute('INSERT INTO sessions VALUES (?,?,?)', (digest(token), email, now+28800))
                success = True
    if not success:
        return jsonify(error='Código inválido ou expirado. Solicite outro código se necessário.'), 400
    response = jsonify(authenticated=True, email=email)
    response.set_cookie(COOKIE, token, max_age=28800, secure=True, httponly=True, samesite='Strict', path='/')
    return response


@blueprint.post('/api/access/logout')
def logout():
    if not secure_origin():
        return jsonify(error='Origem inválida.'), 403
    with connection() as db:
        db.execute('DELETE FROM sessions WHERE value=?', (digest(request.cookies.get(COOKIE, '')),))
    response = jsonify(authenticated=False)
    response.delete_cookie(COOKIE, secure=True, httponly=True, samesite='Strict')
    return response


@blueprint.after_request
def private(response):
    response.headers['Cache-Control'] = 'no-store'
    return response
