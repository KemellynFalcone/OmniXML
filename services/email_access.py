"""Password login and revocable sessions. Module name retained for imports."""
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from urllib.parse import urlsplit

import requests
from flask import Blueprint, jsonify, request, g
from werkzeug.security import generate_password_hash, check_password_hash
from services import client_registry as registry, password_store as passwords

blueprint = Blueprint('email_access', __name__)
COOKIE = 'omnixml_access'
DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32))


def configured():
    return len(os.environ.get('OMNIXML_AUTH_SECRET', '')) >= 32 and registry.enabled() and bool(registry.admins())


def allowed(email):
    return registry.allowed(email)


def digest(value):
    return hmac.new(os.environ.get('OMNIXML_AUTH_SECRET', '').encode(), value.encode(), hashlib.sha256).hexdigest()


@contextmanager
def connection():
    db = sqlite3.connect(os.environ.get('OMNIXML_AUTH_DB', '/tmp/omnixml-auth.sqlite3'), timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS password_sessions (value TEXT PRIMARY KEY, email TEXT, version TEXT, expires INTEGER)')
    db.execute('CREATE TABLE IF NOT EXISTS rates (value TEXT PRIMARY KEY, start INTEGER, count INTEGER)')
    try:
        with db:
            now = int(time.time())
            db.execute('DELETE FROM password_sessions WHERE expires<=?', (now,))
            db.execute('DELETE FROM rates WHERE start<?', (now-3600,))
            # Remove obsolete codes and old sessions from an existing installation.
            db.execute('DROP TABLE IF EXISTS codes')
            db.execute('DROP TABLE IF EXISTS sessions')
        with db:
            yield db
    finally:
        db.close()


def secure_origin():
    origin = urlsplit(request.headers.get('Origin', ''))
    return request.is_secure and origin.scheme == request.scheme and origin.netloc == request.host


def identity():
    # Reuse authorization only within this HTTP request, never across requests.
    if not hasattr(g, '_omnixml_identity'):
        g._omnixml_identity = _identity()
    return g._omnixml_identity


def _identity():
    if not configured() or not request.is_secure:
        return None
    token = request.cookies.get(COOKIE, '')
    if not token or len(token) > 128:
        return None
    with connection() as db:
        row = db.execute('SELECT email,version FROM password_sessions WHERE value=? AND expires>?', (digest(token), int(time.time()))).fetchone()
    if not row or not allowed(row[0]):
        return None
    credential = passwords.credential(row[0])
    return row[0] if credential and credential[0] and hmac.compare_digest(credential[1], row[1]) else None


def captcha_keys():
    return os.environ.get('OMNIXML_RECAPTCHA_SITE_KEY', ''), os.environ.get('OMNIXML_RECAPTCHA_SECRET_KEY', '')


def captcha_site_key():
    site, secret = captcha_keys()
    return site if site and secret else ''


def captcha_valid(token):
    site, secret = captcha_keys()
    if not site and not secret:
        return True
    if not site or not secret or not isinstance(token, str) or not 1 <= len(token) <= 4096:
        return False
    try:
        response = requests.post('https://www.google.com/recaptcha/api/siteverify',
                                 data={'secret':secret, 'response':token}, timeout=(5, 10), allow_redirects=False)
        result = response.json() if response.status_code == 200 else {}
        return (result.get('success') is True and not result.get('error-codes')
                and result.get('hostname') == urlsplit(request.host_url).hostname)
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        return False


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


def attempt(email=''):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        return (rate_limit(db, digest('login-ip:'+(request.remote_addr or 'unknown')), 60)
                and rate_limit(db, digest('login-email:'+email), 10))


@blueprint.before_request
def limit_body():
    request.max_content_length = 8192


@blueprint.get('/api/access/session')
def session_state():
    email = identity()
    return jsonify(configured=configured(), authenticated=bool(email), email=email, admin=email in registry.admins())


@blueprint.post('/api/access/login')
def login():
    if not secure_origin():
        return jsonify(error='Origem inválida.'), 403
    if not configured():
        return jsonify(error='Acesso indisponível. Contate o administrador.'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Requisição inválida.'), 400
    email = str(data.get('email', '')).strip().lower()
    password = data.get('password', '')
    if len(email) > 254 or not isinstance(password, str) or len(password) > passwords.MAX_PASSWORD:
        return jsonify(error='E-mail ou senha inválidos.'), 401
    if not attempt(email):
        return jsonify(error='Muitas tentativas. Aguarde antes de tentar novamente.'), 429, {'Retry-After':'3600'}
    if not captcha_valid(data.get('captcha', '')):
        return jsonify(error='Não foi possível validar a proteção. Marque “Não sou um robô” e tente novamente.'), 400
    passwords.bootstrap(email)
    row = passwords.credential(email)
    valid = check_password_hash(row[0] if row and row[0] else DUMMY_HASH, password)
    if not valid or not row or not allowed(email):
        return jsonify(error='E-mail ou senha inválidos.'), 401
    token = secrets.token_urlsafe(32)
    with connection() as db:
        db.execute('INSERT INTO password_sessions VALUES (?,?,?,?)', (digest(token), email, row[1], int(time.time())+28800))
    response = jsonify(authenticated=True, email=email)
    response.set_cookie(COOKIE, token, max_age=28800, secure=True, httponly=True, samesite='Strict', path='/')
    return response


@blueprint.post('/api/access/activate')
def activate():
    if not secure_origin():
        return jsonify(error='Origem inválida.'), 403
    if not configured():
        return jsonify(error='Acesso indisponível.'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Requisição inválida.'), 400
    token, password = data.get('invite', ''), data.get('password', '')
    if not isinstance(token, str) or not 1 <= len(token) <= 128:
        return jsonify(error='Link inválido, usado ou expirado. Solicite outro ao administrador.'), 400
    if not attempt('activation:'+token):
        return jsonify(error='Muitas tentativas. Aguarde antes de tentar novamente.'), 429
    if not passwords.valid_password(password):
        return jsonify(error='Use uma senha de 15 a 128 caracteres. Uma frase longa é uma boa opção.'), 400
    if not captcha_valid(data.get('captcha', '')):
        return jsonify(error='Valide a proteção “Não sou um robô” e tente novamente.'), 400
    if not isinstance(token, str) or len(token) > 128 or not passwords.activate(token, password):
        return jsonify(error='Link inválido, usado ou expirado. Solicite outro ao administrador.'), 400
    return jsonify(message='Senha salva. Entre com seu e-mail e sua senha.')


@blueprint.post('/api/access/logout')
def logout():
    if not secure_origin():
        return jsonify(error='Origem inválida.'), 403
    with connection() as db:
        db.execute('DELETE FROM password_sessions WHERE value=?', (digest(request.cookies.get(COOKIE, '')),))
    response = jsonify(authenticated=False)
    response.delete_cookie(COOKIE, secure=True, httponly=True, samesite='Strict')
    return response


@blueprint.after_request
def private(response):
    response.headers['Cache-Control'] = 'no-store'
    return response
