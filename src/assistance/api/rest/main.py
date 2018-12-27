# -*- coding: utf-8 -*-
'''
    Confiruro los loggers
'''
import logging
from logging.handlers import TimedRotatingFileHandler
logging.getLogger().setLevel(logging.DEBUG)

import sys
import os
from dateutil import parser

from werkzeug.contrib.fixers import ProxyFix

import flask
from flask import Flask, Response, abort, make_response, jsonify, url_for, request, json, stream_with_context, send_from_directory
from flask_jsontools import jsonapi
from dateutil import parser

VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))

from rest_utils import register_encoder

oidc_url = os.environ['OIDC_URL']
client_id = os.environ['OIDC_CLIENT_ID']
client_secret = os.environ['OIDC_CLIENT_SECRET']
warden_url = os.environ['WARDEN_API_URL']
from warden.sdk.warden import Warden
warden = Warden(oidc_url, warden_url, client_id, client_secret, verify=VERIFY_SSL)

from assistance.model.AssistanceModel import AssistanceModel
from assistance.model import obtener_session

''' configuro el logger para la sincronización de asistencia '''
logger = logging.getLogger('assistance.model.zkSoftware')
hdlr = TimedRotatingFileHandler('/var/log/assistance/sinc_logs_{}.log'.format(os.getpid()), when='D', interval=1)
formatter = logging.Formatter('%(asctime)s, %(name)s, %(module)s, %(filename)s, %(funcName)s, %(levelname)s, %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='/src/assistance/web')
app.wsgi_app = ProxyFix(app.wsgi_app)
register_encoder(app)

API_BASE = os.environ['API_BASE']

@app.route(API_BASE + '/obtener_config', methods=['GET'])
@jsonapi
def retornar_config_ui():
    config = AssistanceModel._config()
    return config['ui']

def _acceso_modulos_modelo(uid):
    return AssistanceModel.obtener_acceso_modulos(uid)


@app.route(API_BASE + '/acceso_modulos', methods=['GET'])
@warden.require_valid_token
@jsonapi
def obtener_acceso_modulos(token=None):
    config = AssistanceModel._config()
    perfiles = config['api']['perfiles']
    for perfil in perfiles:
        p = perfil['perfil']
        response = warden.has_all_profiles(token, [p])
        if 'profile' in response and response['profile']:
            return perfil['funciones']

    """
        se chequea el modelo para controlar si es necesario asignarle ciertas funciones
    """
    autorizador_id = token['sub']
    funciones = AssistanceModel.obtener_acceso_modulos(autorizador_id)
    if funciones:
        return funciones

    """
        si no matcheo anteriorment entonces retorno las funciones por defecto.
    """
    pgen = (p for p in perfiles if p['perfil'] == 'default')
    pdefault = next(pgen)
    if not pdefault or pdefault['perfil'] != 'default':
        raise Exception('no se encuentra perfil por defecto')
    return pdefault['funciones']



@app.route(API_BASE + '/telegram_token', methods=['GET'])
@warden.require_valid_token
@jsonapi
def telegram_token(token=None):
    h = AssistanceModel.telegram_token(token)
    return {
        'status': 'ok',
        'token': h
    }

@app.route(API_BASE + '/telegram_activate/<codigo>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def telegram_activate(codigo, token=None):
    AssistanceModel.telegram_activate(codigo, token)
    return {
        'status': 'ok'
    }


@app.route(API_BASE + '/usuarios/search/<search>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def usuarios_search(search, token=None):

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin','assistance-operator', 'assistance-user'])
    if prof and prof['profile']:
        usuarios = AssistanceModel.usuarios_search(search)
        return usuarios

    autorizador_id = token['sub']
    usuarios = AssistanceModel.sub_usuarios_search(autorizador_id, search)
    return usuarios
    
@app.route(API_BASE + '/usuarios/<uid>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def usuarios(uid=None, token=None):
    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin','assistance-operator', 'assistance-user'])
    if prof and prof['profile'] == True:
        return AssistanceModel.usuario(session, uid, retornarClave=False)

    autorizador_id = token['sub']
    if AssistanceModel.chequear_acceso(autorizador_id, uid):
        return AssistanceModel.usuario(session, uid, retornarClave=False)

    ''' como no soy admin, ni tengo cargo, entonces chequea que se este consultando a si mismo '''
    if autorizador_id == uid:
        return AssistanceModel.usuario(session, autorizador_id, retornarClave=False)

    return ('no tiene los permisos suficientes', 403)


@app.route(API_BASE + '/lugares', methods=['GET'])
@warden.require_valid_token
@jsonapi
def lugares(token=None):
    uid = token['sub']
    search = request.args.get('q')
    if not search:
        search = ''

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin','assistance-operator', 'assistance-user'])
    if prof and prof['profile'] == True:
        config = AssistanceModel._config()
        lid = config['api']['lugar_raiz']
        return AssistanceModel.sublugares_por_lugar_id(lugar_id=lid, search=search)

    return AssistanceModel.lugares(session=None, autorizador_id=uid, search=search)

@app.route(API_BASE + '/usuarios/<uid>/perfil', methods=['GET'])
@warden.require_valid_token
@jsonapi
def perfil(uid, token):
    fecha_str = request.args.get('fecha', None)
    fecha = parser.parse(fecha_str).date() if fecha_str else None
    if not fecha:
        return ('fecha, parametro no encontrado',400)

    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin'])
    if prof and prof['profile']:
        with obtener_session() as session:
            return AssistanceModel.perfil(session, uid, fecha)

    usuario_logueado = token['sub']
    with obtener_session() as session:
        #if AssistanceModel.chequear_acceso_reporte(session, usuario_logueado, uid):
        if usuario_logueado == uid:
            return AssistanceModel.perfil(session, uid, fecha)
        else:
            return ('no tiene los permisos suficientes', 403)


@app.route(API_BASE + '/usuarios/<uid>/reporte', methods=['GET'])
@warden.require_valid_token
@jsonapi
def reporte(uid, token):
    fecha_str = request.args.get('inicio', None)
    inicio = parser.parse(fecha_str).date() if fecha_str else None

    fecha_str = request.args.get('fin', None)
    fin = parser.parse(fecha_str).date() if fecha_str else None

    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin','assistance-operator','assistance-user'])
    if prof and prof['profile']:
        with obtener_session() as session:
            return AssistanceModel.reporte(session, uid, inicio, fin)

    usuario_logueado = token['sub']
    if AssistanceModel.chequear_acceso(usuario_logueado, uid):
        with obtener_session() as session:
                return AssistanceModel.reporte(session, uid, inicio, fin)
    else:
        return ('no tiene los permisos suficientes', 403)

@app.route(API_BASE + '/usuarios/<uid>/justificaciones', methods=['GET'])
@warden.require_valid_token
@jsonapi
def reporte_justificaciones(uid, token):
    fecha_str = request.args.get('inicio', None)
    inicio = parser.parse(fecha_str).date() if fecha_str else None

    fecha_str = request.args.get('fin', None)
    fin = parser.parse(fecha_str).date() if fecha_str else None

    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin','assistance-operator','assistance-user'])
    if prof and prof['profile']:
        with obtener_session() as session:
            return AssistanceModel.reporteJustificaciones(session, uid, inicio, fin)

    usuario_logueado = token['sub']
    if AssistanceModel.chequear_acceso(usuario_logueado, uid):
        with obtener_session() as session:
                return AssistanceModel.reporteJustificaciones(session, uid, inicio, fin)
    return ('no tiene los permisos suficientes', 403)

@app.route(API_BASE + '/reportes', methods=['POST'])
@warden.require_valid_token
@jsonapi
def reporte_general(token):
    datos = request.get_json()
    fecha = parser.parse(datos["fecha"]).date() if 'fecha' in datos else None
    lugares = datos["lugares"]

    usuario_logueado = token['sub']

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin','assistance-operator','assistance-user'])
    if prof and prof['profile'] == True:
        with obtener_session() as session:
            return AssistanceModel.reporteGeneralAdmin(session, lugares, fecha)

    if AssistanceModel.chequear_acceso_lugares(usuario_logueado, lugares):
        with obtener_session() as session:
            return AssistanceModel.reporteGeneral(session, usuario_logueado, lugares, fecha)

    return ('no tiene los permisos suficientes', 403)


@app.route(API_BASE + '/usuarios/<uid>/horario', methods=['GET'])
@warden.require_valid_token
@jsonapi
def horario(uid,token):
    fecha_str = request.args.get('fecha', None)
    fecha = parser.parse(fecha_str).date() if fecha_str else None

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin','assistance-operator','assistance-user'])
    if prof and prof['profile'] == True:
        with obtener_session() as session:
            return AssistanceModel.horario(session, uid, fecha)

    usuario_logueado = token['sub']
    if AssistanceModel.chequear_acceso(usuario_logueado, uid):        
        with obtener_session() as session:
            return AssistanceModel.horario(session, uid, fecha)

    return ('no tiene los permisos suficientes', 403)


@app.route(API_BASE + '/usuarios/<uid>/horario/<hid>', methods=['DELETE'])
@warden.require_valid_token
@jsonapi
def eliminar_horarios(uid, hid, token):

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        ''' como no soy admin, entonces chequea que se este consultando a si mismo '''
        if not uid or uid != token['sub']:
            return ('no tiene los permisos suficientes', 403)

    fecha_str = request.args.get('fecha_inicio', None)
    inicio = parser.parse(fecha_str).date() if fecha_str else None

    fecha_str = request.args.get('fecha_fin', None)
    fin = parser.parse(fecha_str).date() if fecha_str else None

    with obtener_session() as session:
        h = AssistanceModel.eliminar_horario(session, uid, hid)
        session.commit()
    
    return {'status':'ok', 'horario':h}

@app.route(API_BASE + '/usuarios/<uid>/historial_horarios', methods=['GET'])
@warden.require_valid_token
@jsonapi
def historial_horarios(uid, token):

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        ''' como no soy admin, entonces chequea que se este consultando a si mismo '''
        if not uid or uid != token['sub']:
            return ('no tiene los permisos suficientes', 403)

    fecha_str = request.args.get('fecha_inicio', None)
    inicio = parser.parse(fecha_str).date() if fecha_str else None

    fecha_str = request.args.get('fecha_fin', None)
    fin = parser.parse(fecha_str).date() if fecha_str else None

    timezone = request.args.get('timezone', 'America/Argentina/Buenos_Aires')

    with obtener_session() as session:
        ret = AssistanceModel.historial_horarios(session, uid, inicio, fin, timezone)
        return ret



@app.route(API_BASE + '/horario', methods=['PUT'])
@warden.require_valid_token
@jsonapi
def crear_horario(token):
    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    horarios = request.get_json()
    logging.debug(horarios)
    with obtener_session() as session:
        AssistanceModel.crearHorario(session, horarios)
        session.commit()
        return  True

import datetime

@app.route(API_BASE + '/usuarios/<uid>/logs', methods=['GET'])
@warden.require_valid_token
@jsonapi
def logs_por_usuario(uid,token):
   
    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin', 'assistance-operator'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    inicio = datetime.datetime.now()
    fin = inicio + datetime.timedelta(days=1)
    marcaciones = []
    with obtener_session() as session:
        reporte = AssistanceModel.reporte(session, uid=uid, inicio=inicio, fin=fin)
        for r in reporte.reportes:
            marcaciones.extend(r.marcaciones)
            marcaciones.extend(r.duplicadas)
    return marcaciones

@app.route(API_BASE + '/usuarios/<uid>/logs', methods=['POST'])
@warden.require_valid_token
@jsonapi
def crear_log_por_usuario(uid, token=None):
    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    with obtener_session() as session:
        r = AssistanceModel.crear_log_por_usuario(session, uid)
        session.commit()
        return r

@app.route(API_BASE + '/logs/<fecha>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def logs_por_fecha(fecha,token):
    #return AssistanceModel.reporte(uid=uid, inicio=inicio, fin=fin)
    return None

@app.route(API_BASE + '/relojes', methods=['GET'])
@warden.require_valid_token
@jsonapi
def relojes(token):
    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

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
@warden.require_valid_token
@jsonapi
def reloj(rid,token):
    assert rid is not None

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

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
@warden.require_valid_token
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
@warden.require_valid_token
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
@warden.require_valid_token
@jsonapi
def reloj_usuarios(rid, token):

    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    assert rid is not None
    with obtener_session() as session:
        r = AssistanceModel.usuarios_por_reloj(session, rid)
        return r

@app.route(API_BASE + '/relojes/<rid>/usuarios/<ruid>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def reloj_usuario(rid, ruid, token):
    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
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
@warden.require_valid_token
@jsonapi
def reloj_huellas(rid, token):
    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    assert rid is not None
    with obtener_session() as session:
        r = AssistanceModel.templates_por_reloj(session, rid)
        return r


@app.route(API_BASE + '/justificaciones/<jid>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def justificacion(jid, token):
    with obtener_session() as session:
        return AssistanceModel.justificacion(session, jid)

@app.route(API_BASE + '/justificaciones', methods=['GET'])
@warden.require_valid_token
@jsonapi
def justificaciones(token):
    with obtener_session() as session:
        return AssistanceModel.justificaciones(session)

@app.route(API_BASE + '/justificaciones', methods=['PUT'])
@warden.require_valid_token
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
@warden.require_valid_token
@jsonapi
def eliminar_justificacion(jid, token):
    prof = warden.has_one_profile(token, ['assistance-super-admin','assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)
    with obtener_session() as session:
        AssistanceModel.eliminarJustificacion(session, jid)
        session.commit()

@app.route(API_BASE + '/justificaciones/<jid>', methods=['POST'])
@warden.require_valid_token
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
@warden.require_valid_token
@jsonapi
def justificar(token):
    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin','assistance-operator'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)
    fechaJustificada = request.get_json()
    logging.debug(fechaJustificada)
    with obtener_session() as session:
        autorizador_id = token['sub']
        id = AssistanceModel.justificar(session, fechaJustificada, autorizador_id)
        session.commit()
        return id

@app.route(API_BASE + '/usuarios/<uid>/justificaciones/<jid>', methods=['DELETE'])
@warden.require_valid_token
@jsonapi
def eliminar_fecha_justificada(uid, jid, token):
    prof = warden.has_one_profile(token, ['assistance-super-admin', 'assistance-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)
    with obtener_session() as session:
        autorizador_id = token['sub']
        jid = AssistanceModel.eliminarFechaJustificada(session, jid, autorizador_id)
        session.commit()
        return jid

@app.route(API_BASE + '/compensatorios/<uid>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def compensatorios(uid, token):
    assert uid is not None

    prof = warden.has_one_profile(token, ['assistance-super-admin'])
    if not prof or prof['profile'] == False:
        ''' Como no es admin compruebo si es una autoconsulta '''
        if uid != token['sub']:
            return ('no tiene los permisos suficientes', 403)

    with obtener_session() as session:
        return AssistanceModel.compensatorios(session, uid)

@app.route(API_BASE + '/compensatorios', methods=['PUT'])
@warden.require_valid_token
@jsonapi
def crear_compensatorio(token):
    prof = warden.has_one_profile(token, ['assistance-super-admin'])
    if not prof or prof['profile'] == False:
        return ('no tiene los permisos suficientes', 403)

    id_creador_compensatorio = token['sub']

    compensatorio = request.get_json()
    logging.debug(compensatorio)
    with obtener_session() as session:
        cid = AssistanceModel.crear_compensatorio(session, compensatorio, id_creador_compensatorio)
        session.commit()
        return cid

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
    app.run(host='0.0.0.0', port=10302, debug=False)

if __name__ == '__main__':
    main()
