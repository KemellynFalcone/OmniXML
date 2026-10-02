import re
from flask import Blueprint, jsonify, redirect, render_template, request
from services import client_registry as registry
from services.email_access import identity, secure_origin
from services.traffic_monitor import snapshot

blueprint = Blueprint('administration', __name__)


def administrator():
    return request.is_secure and identity() in registry.admins()


@blueprint.get('/login')
def login():
    if identity():
        return redirect('/downloads')
    return render_template('login.html')


@blueprint.get('/privacy')
def privacy():
    return render_template('privacy.html')


@blueprint.get('/admin')
def admin():
    if not identity():
        return redirect('/login')
    if not administrator():
        return 'Acesso restrito ao administrador.',403
    return render_template('admin.html')


@blueprint.get('/api/admin/clients')
def clients():
    if not administrator():
        return jsonify(error='Acesso restrito.'),403
    return jsonify(clients=registry.list_clients(), editable=registry.enabled())


@blueprint.post('/api/admin/clients')
def change_client():
    if not administrator() or not secure_origin():
        return jsonify(error='Acesso restrito.'),403
    request.max_content_length = 4096
    if not registry.enabled():
        return jsonify(error='Configure OMNIXML_CLIENTS_DB em armazenamento persistente antes de cadastrar clientes.'),503
    data = request.get_json(silent=True)
    if not isinstance(data,dict):
        return jsonify(error='Requisição inválida.'),400
    email = str(data.get('email','')).strip().lower()
    action = data.get('action')
    if len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or action not in ('add','block','enable','delete'):
        return jsonify(error='E-mail ou ação inválida.'),400
    try:
        registry.change(email,action)
    except ValueError as error:
        return jsonify(error=str(error)),400
    # Expire pending authentication and all existing sessions on block/delete.
    if action in ('block','delete'):
        from services.email_access import connection
        with connection() as db:
            db.execute('DELETE FROM codes WHERE email=?',(email,))
            db.execute('DELETE FROM sessions WHERE email=?',(email,))
    return jsonify(ok=True)


@blueprint.get('/api/admin/traffic')
def traffic():
    if not administrator():
        return jsonify(error='Acesso restrito.'),403
    return jsonify(snapshot())


@blueprint.after_request
def private(response):
    response.headers['Cache-Control']='no-store'
    return response
