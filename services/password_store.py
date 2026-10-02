"""Durable password hashes and one-use invitations; no fiscal content."""
import os
import secrets
import time
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
from services import client_registry as registry

MIN_PASSWORD = 15
MAX_PASSWORD = 128


def valid_password(password):
    return isinstance(password, str) and MIN_PASSWORD <= len(password) <= MAX_PASSWORD


@contextmanager
def connection():
    with registry.connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS credentials (email TEXT PRIMARY KEY, password_hash TEXT NOT NULL, version TEXT NOT NULL, invite_digest TEXT UNIQUE, invite_expires BIGINT NOT NULL)')
        yield db


def credential(email):
    with connection() as db:
        return db.execute('SELECT password_hash,version FROM credentials WHERE email=?', (email,)).fetchone()


def bootstrap(email):
    """Seed an explicitly configured owner once; never overwrite their password."""
    password = os.environ.get('OMNIXML_ADMIN_INITIAL_PASSWORD', '')
    if email not in registry.admins() or not valid_password(password) or credential(email):
        return
    with connection() as db:
        db.execute('INSERT INTO credentials (email,password_hash,version,invite_digest,invite_expires) VALUES (?,?,?,NULL,0) ON CONFLICT(email) DO NOTHING',
                   (email, generate_password_hash(password), secrets.token_hex(16)))


def invite(email):
    from services.email_access import digest
    if not registry.allowed(email):
        raise ValueError('Libere o cliente antes de gerar o link.')
    token = secrets.token_urlsafe(32)
    expires = int(time.time()) + 3600
    with connection() as db:
        db.execute('INSERT INTO credentials (email,password_hash,version,invite_digest,invite_expires) VALUES (?,\'\',?,?,?) ON CONFLICT(email) DO UPDATE SET invite_digest=excluded.invite_digest,invite_expires=excluded.invite_expires',
                   (email, secrets.token_hex(16), digest('invite:'+token), expires))
    return token, expires


def activate(token, password):
    from services.email_access import digest
    key = digest('invite:'+token)
    now = int(time.time())
    with connection() as db:
        row = db.execute('SELECT email FROM credentials WHERE invite_digest=? AND invite_expires>?', (key, now)).fetchone()
    if not row or not registry.allowed(row[0]):
        return False
    hashed = generate_password_hash(password)
    with connection() as db:
        # Conditional update consumes the invitation atomically, including D1.
        result = db.execute('UPDATE credentials SET password_hash=?,version=?,invite_digest=NULL,invite_expires=0 WHERE email=? AND invite_digest=? AND invite_expires>?',
                            (hashed, secrets.token_hex(16), row[0], key, int(time.time())))
    return bool(result.rowcount)


def revoke(email, delete=False):
    with connection() as db:
        if delete:
            db.execute('DELETE FROM credentials WHERE email=?', (email,))
        else:
            db.execute('UPDATE credentials SET version=?,invite_digest=NULL,invite_expires=0 WHERE email=?', (secrets.token_hex(16), email))
