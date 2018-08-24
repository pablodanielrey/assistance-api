# -*- coding: utf-8 -*-
'''
    Confiruro los loggers
'''
import logging
logging.getLogger().setLevel(logging.DEBUG)

import sys
import os
from dateutil import parser

from werkzeug.contrib.fixers import ProxyFix

import flask
from flask import Flask, Response, abort, make_response, jsonify, url_for, request, json, stream_with_context
from flask_jsontools import jsonapi
from dateutil import parser

VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))

from rest_utils import register_encoder

import oidc
from oidc.oidc import TokenIntrospection
client_id = os.environ['OIDC_CLIENT_ID']
client_secret = os.environ['OIDC_CLIENT_SECRET']
rs = TokenIntrospection(client_id, client_secret, verify=VERIFY_SSL)

warden_url = os.environ['WARDEN_API_URL']
from warden.sdk.warden import Warden
warden = Warden(warden_url, client_id, client_secret, verify=VERIFY_SSL)

from assistance.model.AssistanceModel import AssistanceModel
from assistance.model import obtener_session

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='/src/assistance/web')
app.wsgi_app = ProxyFix(app.wsgi_app)
register_encoder(app)

API_BASE = os.environ['API_BASE']

@app.route(API_BASE + '/acceso_modulos', methods=['GET'])
@rs.require_valid_token
@jsonapi
def obtener_acceso_modulos(token=None):

    prof = warden.has_one_profile(token, ['assistance-admin'])
    if prof and prof['profile'] == True:
        a = [
            'inicio_personal',
            'reporte_personal',
            'reporte_general',
            'justificacion_personal',
            'justificacion_general',
            'justificacion_tipo_abm',
            'horario_vista',
            'horario_abm'
        ]
        return json.dumps(a)
    
    prof = warden.has_one_profile(token, ['assistance-operator'])
    if prof and prof['profile'] == True:
        a = [
            'inicio_personal',
            'reporte_personal',
            'reporte_general',
            'justificacion_personal',
            'justificacion_general',
            'horario_vista'
        ]
        return json.dumps(a)

    a = [
        'inicio_personal'
    ]
    return json.dumps(a)            

@app.route(API_BASE + '/usuarios', methods=['GET'])
@app.route(API_BASE + '/usuarios/<uid>', methods=['GET'])
@rs.require_valid_token
@jsonapi
def usuarios(uid=None, token=None):

    # access = w.check_access(token, 'rn:assistance:users', 'list')
    # if not access:
    #     return ('no tiene los permisos suficientes', 403)
    
    prof = warden.has_one_profile(token, ['assistance-admin'])
    if not prof or prof['profile'] == False:
        ''' como no soy admin, entonces chequea que se este consultando a si mismo '''
        if not uid or uid != token['sub']:
            return ('no tiene los permisos suficientes', 403)

    search = request.args.get('q',None)
    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)
    only_internal = request.args.get('assistance',False,bool)
    c = request.args.get('c',False,bool)
    with obtener_session() as session:
        if uid:
            return AssistanceModel.usuario(session, uid, retornarClave=c)
        else:
            fecha_str = request.args.get('f', None)
            fecha = parser.parse(fecha_str) if fecha_str else None
            usuarios = AssistanceModel.usuarios(session, search=search, retornarClave=c, offset=offset, limit=limit, fecha=fecha)
            if not only_internal:
                return usuarios
            else:
                ''' retorno solo los usuarios que tienen algun registro de asistencia '''
                return [u for u in usuarios if 'asistencia' in u and u['asistencia'] is not None]

@app.route(API_BASE + '/lugares', methods=['GET'])
@rs.require_valid_token
@jsonapi
def lugares(token=None):
    with obtener_session() as session:
        search = request.args.get('q')
        return AssistanceModel.lugares(session=session, search=search)

@app.route(API_BASE + '/usuarios/<uid>/reporte', methods=['GET'])
@rs.require_valid_token
@jsonapi
def reporte(uid, token):
    fecha_str = request.args.get('inicio', None)
    inicio = parser.parse(fecha_str).date() if fecha_str else None

    fecha_str = request.args.get('fin', None)
    fin = parser.parse(fecha_str).date() if fecha_str else None

    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin'])
    if prof and prof['profile']:
        with obtener_session() as session:
            return AssistanceModel.reporte(session, uid, inicio, fin)

    usuario_logueado = token['sub']
    with obtener_session() as session:
        if AssistanceModel.chequear_acceso_reporte(session, usuario_logueado, uid):
            return AssistanceModel.reporte(session, uid, inicio, fin)
        else:
            return ('no tiene los permisos suficientes', 403)

@app.route(API_BASE + '/reportes', methods=['POST'])
@rs.require_valid_token
@jsonapi
def reporte_general(token):

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    datos = request.get_json()
    fecha = parser.parse(datos["fecha"]).date() if 'fecha' in datos else None
    lugares = datos["lugares"]
    logging.info(lugares)
    with obtener_session() as session:
        return AssistanceModel.reporteGeneral(session, lugares, fecha)

@app.route(API_BASE + '/usuarios/<uid>/horario', methods=['GET'])
@rs.require_valid_token
@jsonapi
def horario(uid,token):
    prof = warden.has_one_profile(token, ['assistance-admin'])
    if not prof or prof['profile'] == False:
        ''' como no soy admin, entonces chequea que se este consultando a si mismo '''
        if not uid or uid != token['sub']:
            return ('no tiene los permisos suficientes', 403)
    fecha_str = request.args.get('fecha', None)
    fecha = parser.parse(fecha_str).date() if fecha_str else None
    with obtener_session() as session:
        return AssistanceModel.horario(session, uid, fecha)

@app.route(API_BASE + '/horario', methods=['PUT'])
@rs.require_valid_token
@jsonapi
def crear_horario(token):

    prof = warden.has_one_profile(token, ['assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    horarios = request.get_json()
    logging.debug(horarios)
    with obtener_session() as session:
        AssistanceModel.crearHorario(session, horarios)
        session.commit()
        return  True

@app.route(API_BASE + '/usuarios/<uid>/logs', methods=['GET'])
@rs.require_valid_token
@jsonapi
def logs_por_usuario(uid,token):
    #return AssistanceModel.reporte(uid=uid, inicio=inicio, fin=fin)
    return None

@app.route(API_BASE + '/logs/<fecha>', methods=['GET'])
@rs.require_valid_token
@jsonapi
def logs_por_fecha(fecha,token):
    #return AssistanceModel.reporte(uid=uid, inicio=inicio, fin=fin)
    return None

@app.route(API_BASE + '/relojes', methods=['GET'])
@jsonapi
def relojes():
    with obtener_session() as session:
        return AssistanceModel.relojes(session)

@app.route(API_BASE + '/relojes/sincronizar', methods=['GET'])
@jsonapi
def relojes_sincronizar():
    with obtener_session() as session:
        r = AssistanceModel.sincronizar(session)
        session.commit()
        return r

@app.route(API_BASE + '/relojes/<rid>', methods=['GET'])
@jsonapi
def reloj(rid):
    assert rid is not None
    with obtener_session() as session:
        r = AssistanceModel.reloj(session, rid)
        return r

@app.route(API_BASE + '/relojes/<rid>/sincronizar', methods=['GET'])
#@jsonapi
def reloj_sincronizar(rid):
    def generate():
        assert rid is not None
        with obtener_session() as session:
            for r in AssistanceModel.sincronizar_reloj(session, rid):
                session.commit()
                yield flask.json.dumps(r) + "\n"
    return Response(stream_with_context(generate()), mimetype='application/stream+json')

@app.route(API_BASE + '/relojes/<rid>/marcaciones', methods=['GET'])
@jsonapi
def reloj_marcaciones(rid):
    assert rid is not None
    with obtener_session() as session:
        r = AssistanceModel.marcaciones_por_reloj(session, rid)
        return r


@app.route(API_BASE + '/relojes/<rid>/huellas', methods=['DELETE'])
@rs.require_valid_token
@jsonapi
def reloj_eliminar_huellas(rid, token):

    prof = warden.has_one_profile(token, 'assistance-super-admin')
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    assert rid is not None
    with obtener_session() as session:
        r = AssistanceModel.eliminar_huellas_reloj(session, rid)
        return r

@app.route(API_BASE + '/relojes/<rid>/usuarios', methods=['DELETE'])
@rs.require_valid_token
@jsonapi
def reloj_eliminar_usuarios(rid, token):
    prof = warden.has_one_profile(token, 'assistance-super-admin')
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    assert rid is not None
    with obtener_session() as session:
        r = AssistanceModel.eliminar_usuarios_reloj(session, rid)
        return r

@app.route(API_BASE + '/relojes/<rid>/usuarios', methods=['GET'])
@rs.require_valid_token
@jsonapi
def reloj_usuarios(rid, token):

    prof = warden.has_one_profile(token, ['assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    assert rid is not None
    with obtener_session() as session:
        r = AssistanceModel.usuarios_por_reloj(session, rid)
        return r

@app.route(API_BASE + '/relojes/<rid>/usuarios/<ruid>', methods=['GET'])
@rs.require_valid_token
@jsonapi
def reloj_usuario(rid, ruid, token):

    prof = warden.has_one_profile(token, ['assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    assert rid is not None
    assert ruid is not None
    with obtener_session() as session:
        u = AssistanceModel.usuario_por_reloj(session, rid, ruid)
        t = AssistanceModel.templates_por_usuario_por_reloj(session, rid, ruid)
        r = {
            'usuario': u,
            'huellas': t
        }
        return r

@app.route(API_BASE + '/relojes/<rid>/huellas', methods=['GET'])
@rs.require_valid_token
@jsonapi
def reloj_huellas(rid, token):
    prof = warden.has_one_profile(token, ['assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    assert rid is not None
    with obtener_session() as session:
        r = AssistanceModel.templates_por_reloj(session, rid)
        return r


@app.route(API_BASE + '/justificaciones/<jid>', methods=['GET'])
@rs.require_valid_token
@jsonapi
def justificacion(jid, token):
    with obtener_session() as session:
        return AssistanceModel.justificacion(session, jid)

@app.route(API_BASE + '/justificaciones', methods=['GET'])
@rs.require_valid_token
@jsonapi
def justificaciones(token):
    with obtener_session() as session:
        return AssistanceModel.justificaciones(session)

@app.route(API_BASE + '/justificaciones', methods=['PUT'])
@rs.require_valid_token
@jsonapi
def crear_justificacion(token):
    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    justificacion = request.get_json()
    logging.debug(justificacion)
    with obtener_session() as session:
        jid = AssistanceModel.crear_justificacion(session, justificacion)
        session.commit()
        return jid

@app.route(API_BASE + '/justificaciones/<jid>', methods=['DELETE'])
@rs.require_valid_token
@jsonapi
def eliminar_justificacion(jid, token):
    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)
    with obtener_session() as session:
        AssistanceModel.eliminarJustificacion(session, jid)
        session.commit()

@app.route(API_BASE + '/justificaciones/<jid>', methods=['POST'])
@rs.require_valid_token
@jsonapi
def actualizar_justificacion(jid, token):
    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)
    datos = request.get_json()
    with obtener_session() as session:
        AssistanceModel.actualizar_justificacion(session, jid, datos)
        session.commit()

@app.route(API_BASE + '/justificar', methods=['PUT'])
@rs.require_valid_token
@jsonapi
def justificar(token):
    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)
    fechaJustificada = request.get_json()
    logging.debug(fechaJustificada)
    with obtener_session() as session:
        id = AssistanceModel.justificar(session, fechaJustificada)
        session.commit()
        return id

@app.route(API_BASE + '/usuarios/<uid>/justificaciones/<jid>', methods=['DELETE'])
@rs.require_valid_token
@jsonapi
def eliminar_fecha_justificada(uid, jid, token):
    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)
    with obtener_session() as session:
        jid = AssistanceModel.eliminarFechaJustificada(session, jid)
        session.commit()
        return jid

@app.route(API_BASE + '*', methods=['OPTIONS'])
def options():
    if request.method == 'OPTIONS':
        return 204
    return 204

@app.after_request
def cors_after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'

    return r

def main():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
