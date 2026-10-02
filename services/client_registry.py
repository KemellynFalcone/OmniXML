"""Minimal access registry; fiscal files never enter this database."""
import os
import sqlite3
import time
from contextlib import contextmanager
from email.utils import parseaddr


def admins():
    explicit = os.environ.get('OMNIXML_ADMIN_EMAILS')
    values = explicit if explicit is not None else parseaddr(os.environ.get('OMNIXML_EMAIL_FROM', ''))[1]
    return {e.strip().lower() for e in values.split(',') if e.strip()}


def legacy():
    return {e.strip().lower() for e in os.environ.get('OMNIXML_ALLOWED_EMAILS', '').split(',') if e.strip()}


def enabled():
    return bool(os.environ.get('OMNIXML_CLIENTS_DB'))


@contextmanager
def connection():
    # No silently ephemeral client list: admin must select storage explicitly.
    path = os.environ['OMNIXML_CLIENTS_DB']
    db = sqlite3.connect(path, timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS clients (email TEXT PRIMARY KEY, active INTEGER NOT NULL, created INTEGER NOT NULL)')
    try:
        with db:
            yield db
    finally:
        db.close()


def allowed(email):
    if email in admins() or email in legacy():
        return True
    if not enabled():
        return False
    with connection() as db:
        row = db.execute('SELECT active FROM clients WHERE email=?', (email,)).fetchone()
    return bool(row and row[0])


def list_clients():
    rows = []
    if enabled():
        with connection() as db:
            rows = [{'email':r[0], 'active':bool(r[1]), 'created':r[2], 'source':'registry'}
                    for r in db.execute('SELECT email,active,created FROM clients ORDER BY email')]
    rows += [{'email':email, 'active':True, 'created':None, 'source':'configuration'} for email in sorted(legacy() | admins())]
    return rows


def change(email, action):
    if email in admins() or email in legacy():
        raise ValueError('Este e-mail está na configuração do servidor. Altere a variável correspondente no Render.')
    with connection() as db:
        if action == 'add':
            db.execute('INSERT INTO clients VALUES (?,1,?) ON CONFLICT(email) DO UPDATE SET active=1', (email, int(time.time())))
        elif action in ('block', 'enable'):
            if not db.execute('UPDATE clients SET active=? WHERE email=?', (int(action=='enable'),email)).rowcount:
                raise ValueError('Cliente não encontrado.')
        elif action == 'delete':
            db.execute('DELETE FROM clients WHERE email=?', (email,))
