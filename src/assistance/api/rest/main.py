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

from rest_utils import register_encoder

import oidc
from oidc.oidc import TokenIntrospection
client_id = os.environ['OIDC_CLIENT_ID']
client_secret = os.environ['OIDC_CLIENT_SECRET']
rs = TokenIntrospection(client_id, client_secret)

from assistance.model.AssistanceModel import AssistanceModel
from assistance.model import Session

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='/src/assistance/web')
app.wsgi_app = ProxyFix(app.wsgi_app)
register_encoder(app)

API_BASE = os.environ['API_BASE']

@app.route(API_BASE + '*', methods=['OPTIONS'])
def options():
    if request.method == 'OPTIONS':
        return 204
    return 204

@app.route(API_BASE + '/usuarios/', methods=['GET'])
@app.route(API_BASE + '/usuarios/<uid>', methods=['GET'])
@rs.require_valid_token
@jsonapi
def usuarios(uid=None, token=None):

    from warden.sdk.warden import Warden
    w = Warden('https://api.econo.unlp.edu.ar/warden/api/v1.0', client_id, client_secret)
    access = w.check_access(token, 'rn:assistance:users', 'list')
    if not access:
        raise Exception('no tiene los permisos suficientes')
    
    prof = w.has_profile(token, 'admin-assistance')
    if not prof or prof['profile'] == False:
        raise Exception('no tiene los permisos suficientes')

    search = request.args.get('q',None)
    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)
    only_internal = request.args.get('assistance',False,bool)
    c = request.args.get('c',False,bool)
    session = Session()
    try:
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
    finally:
        session.close()

@app.route(API_BASE + '/lugares/', methods=['GET'])
@rs.require_valid_token
@jsonapi
def lugares(token=None):
    s = Session()
    try:
        search = request.args.get('q')
        return AssistanceModel.lugares(session=s, search=search)
    except Exception as e:
        logging.exception(e)
        raise e
    finally:
        s.close()

@app.route(API_BASE + '/usuarios/<uid>/reporte/', methods=['GET'])
@rs.require_valid_token
@jsonapi
def reporte(uid, token):
    fecha_str = request.args.get('inicio', None)
    inicio = parser.parse(fecha_str).date() if fecha_str else None

    fecha_str = request.args.get('fin', None)
    fin = parser.parse(fecha_str).date() if fecha_str else None

    session = Session()
    try:
        return AssistanceModel.reporte(session, uid, inicio, fin)
    finally:
        session.close()

@app.route(API_BASE + '/reportes/', methods=['POST'])
@rs.require_valid_token
@jsonapi
def reporte_general(token):
    datos = request.get_json()
    fecha = parser.parse(datos["fecha"]).date() if 'fecha' in datos else None
    lugares = datos["lugares"]
    logging.info(lugares)
    session = Session()
    try:
        return AssistanceModel.reporteGeneral(session, lugares, fecha)
    finally:
        session.close()

@app.route(API_BASE + '/usuarios/<uid>/horario/', methods=['GET'])
@rs.require_valid_token
@jsonapi
def horario(uid,token):
    fecha_str = request.args.get('fecha', None)
    fecha = parser.parse(fecha_str).date() if fecha_str else None

    session = Session()
    try:
        return AssistanceModel.horario(session, uid, fecha)
    finally:
        session.close()

@app.route(API_BASE + '/horario/', methods=['PUT'])
@rs.require_valid_token
@jsonapi
def crear_horario(token):
    horarios = request.get_json()
    logging.debug(horarios)
    session = Session()
    try:
        AssistanceModel.crearHorario(session, horarios)
        session.commit()
        return  True
    finally:
        session.close()

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
    session = Session()
    try:
        return AssistanceModel.relojes(session)
    finally:
        session.close()

@app.route(API_BASE + '/relojes/sincronizar', methods=['GET'])
@jsonapi
def relojes_sincronizar():
    session = Session()
    try:
        r = AssistanceModel.sincronizar(session)
        session.commit()
        return r

    finally:
        session.close()

@app.route(API_BASE + '/relojes/<rid>', methods=['GET'])
@jsonapi
def reloj(rid):
    assert rid is not None
    session = Session()
    try:
        r = AssistanceModel.reloj(session, rid)
        return r

    finally:
        session.close()

@app.route(API_BASE + '/relojes/<rid>/sincronizar', methods=['GET'])
#@jsonapi
def reloj_sincronizar(rid):
    def generate():
        assert rid is not None
        session = Session()
        try:
            for r in AssistanceModel.sincronizar_reloj(session, rid):
                session.commit()
                yield flask.json.dumps(r) + "\n"

        finally:
            session.close()
    return Response(stream_with_context(generate()), mimetype='application/stream+json')

@app.route(API_BASE + '/relojes/<rid>/marcaciones', methods=['GET'])
@jsonapi
def reloj_marcaciones(rid):
    assert rid is not None
    session = Session()
    try:
        r = AssistanceModel.marcaciones_por_reloj(session, rid)
        return r

    finally:
        session.close()


@app.route(API_BASE + '/relojes/<rid>/eliminar_huellas', methods=['GET'])
@rs.require_valid_token
@jsonapi
def reloj_eliminar_huellas(rid, token):
    assert rid is not None
    session = Session()
    try:
        r = AssistanceModel.eliminar_huellas_reloj(session, rid)
        return r

    finally:
        session.close()

@app.route(API_BASE + '/relojes/<rid>/eliminar_usuarios', methods=['GET'])
@rs.require_valid_token
@jsonapi
def reloj_eliminar_usuarios(rid, token):
    assert rid is not None
    session = Session()
    try:
        r = AssistanceModel.eliminar_usuarios_reloj(session, rid)
        return r

    finally:
        session.close()

@app.route(API_BASE + '/relojes/<rid>/usuarios', methods=['GET'])
@rs.require_valid_token
@jsonapi
def reloj_usuarios(rid, token):
    assert rid is not None
    session = Session()
    try:
        r = AssistanceModel.usuarios_por_reloj(session, rid)
        return r

    finally:
        session.close()

@app.route(API_BASE + '/relojes/<rid>/usuarios/<ruid>', methods=['GET'])
@jsonapi
def reloj_usuario(rid, ruid):
    assert rid is not None
    assert ruid is not None
    session = Session()
    try:
        u = AssistanceModel.usuario_por_reloj(session, rid, ruid)
        t = AssistanceModel.templates_por_usuario_por_reloj(session, rid, ruid)
        r = {
            'usuario': u,
            'huellas': t
        }
        return r

    finally:
        session.close()

@app.route(API_BASE + '/relojes/<rid>/huellas', methods=['GET'])
@jsonapi
def reloj_huellas(rid):
    assert rid is not None
    session = Session()
    try:
        r = AssistanceModel.templates_por_reloj(session, rid)
        return r

    finally:
        session.close()


@app.route(API_BASE + '/justificaciones/<jid>', methods=['GET'])
@jsonapi
def justificacion(jid):
    session = Session()
    try:
        return AssistanceModel.justificacion(session, jid)
    finally:
        session.close()

@app.route(API_BASE + '/justificaciones', methods=['GET'])
@jsonapi
def justificaciones():
    session = Session()
    try:
        return AssistanceModel.justificaciones(session)
    finally:
        session.close()

@app.route(API_BASE + '/justificaciones', methods=['PUT'])
@rs.require_valid_token
@jsonapi
def crear_justificacion(token):
    justificacion = request.get_json()
    logging.debug(justificacion)
    session = Session()
    try:
        jid = AssistanceModel.crear_justificacion(session, justificacion)
        session.commit()
        return jid

    finally:
        session.close()

@app.route(API_BASE + '/justificaciones/<jid>', methods=['DELETE'])
@rs.require_valid_token
@jsonapi
def eliminar_justificacion(jid, token):
    session = Session()
    try:
        AssistanceModel.eliminarJustificacion(session, jid)
        session.commit()
    finally:
        session.close()

@app.route(API_BASE + '/justificaciones/<jid>', methods=['POST'])
@rs.require_valid_token
@jsonapi
def actualizar_justificacion(jid, token):
    datos = request.get_json()
    session = Session()
    try:
        AssistanceModel.actualizar_justificacion(session, jid, datos)
        session.commit()

    finally:
        session.close()



@app.route(API_BASE + '/justificar', methods=['PUT'])
@rs.require_valid_token
@jsonapi
def justificar(token):
    fechaJustificada = request.get_json()
    logging.debug(fechaJustificada)
    session = Session()
    try:
        id = AssistanceModel.justificar(session, fechaJustificada)
        session.commit()
        return id

    finally:
        session.close()

@app.route(API_BASE + '/usuarios/<uid>/justificaciones/<jid>', methods=['DELETE'])
@rs.require_valid_token
@jsonapi
def eliminar_fecha_justificada(uid, jid, token):
    session = Session()
    try:
        jid = AssistanceModel.eliminarFechaJustificada(session, jid)
        session.commit()
        return jid
    finally:
        session.close()


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
