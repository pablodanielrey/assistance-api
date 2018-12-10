from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, with_polymorphic
from datetime import datetime, date, timedelta
import requests
import os
import re
import uuid
from dateutil import parser
import datetime
import hashlib

import logging
logger = logging.getLogger('assistance.model.zkSoftware')

import oidc
from oidc.oidc import ClientCredentialsGrant

"""
    ###############
    para la cache de usuarios
"""
from model_utils.API import API
from model_utils.UserCache import UserCache
from model_utils.UsersAPI import UsersAPI
"""
    ###############
"""

from assistance.model.zkSoftware import ZkSoftware
from .entities import *
from .AsientosModel import CompensatoriosModel

import json
import redis
REDIS_HOST = os.environ.get('TELEGRAM_BOT_REDIS')
REDIS_PORT = int(os.environ.get('TELEGRAM_BOT_REDIS_PORT', 6379))
VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))


SILEG_API = os.environ['SILEG_API_URL']
USERS_API = os.environ['USERS_API_URL']
OIDC_URL = os.environ['OIDC_URL']
OIDC_CLIENT_ID = os.environ['OIDC_CLIENT_ID']
OIDC_CLIENT_SECRET = os.environ['OIDC_CLIENT_SECRET']

_API = API(url=OIDC_URL, 
              client_id=OIDC_CLIENT_ID, 
              client_secret=OIDC_CLIENT_SECRET, 
              verify_ssl=VERIFY_SSL)

_USERS_API = UsersAPI(api_url=USERS_API, api=_API)

class AssistanceModel:


    verify = VERIFY_SSL
    sileg_url = SILEG_API
    users_url = USERS_API
    oidc_url = OIDC_URL
    client_id = OIDC_CLIENT_ID
    client_secret = OIDC_CLIENT_SECRET
    eliminar_logs_relojes = bool(int(os.environ.get('ASSISTANCE_DELETE_LOGS_SINC',0)))

    api = _API
    users_api = _USERS_API
    cache_usuarios = UserCache(host=REDIS_HOST, 
                                port=REDIS_PORT, 
                                user_getter=_USERS_API._get_user_uuid,
                                users_getter=_USERS_API._get_users_uuid,
                                user_getter_dni=_USERS_API._get_user_dni)
   

    redis_assistance = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


    @classmethod
    def chequear_acceso_reporte(cls, session, usuario_logueado, uid):
        assert usuario_logueado is not None
        assert uid is not None

        ''' ahora chequeamos que el usuario logueado tenga permisos para consultar los reportes de uid '''

        return usuario_logueado == uid


    """
    ////////////// MANEJO DE CACHE ////////////////////////
    """

    @classmethod
    def _codificar_para_redis(cls, d):
        d2 = {}
        for k in d.keys():
            if d[k] is None:
                d2[k] = 'none_existentvalue'
            elif d[k] == False:
                d2[k] = 'false_existentvalue'
            elif d[k] == True:
                d2[k] = 'true_existentvalue'
            else:
                d2[k] = d[k]
        return d2

    @classmethod
    def _decodificar_desde_redis(cls, d):
        d2 = {}
        for k in d.keys():
            if d[k] == 'none_existentvalue':
                d2[k] = None
            elif d[k] == 'false_existentvalue':
                d2[k] = False
            elif d[k] == 'true_existentvalue':
                d2[k] = True
            else:
                d2[k] = d[k]
        return d2


    """
    /////////////////////////////
    """
    @classmethod
    def telegram_token(cls, token):
        st = token['sub'] + str(datetime.datetime.now())
        h = hashlib.sha1(st.encode('utf-8')).hexdigest()

        usr = cls.cache_usuarios.obtener_usuario_por_uid(token['sub'])
        token['nombre'] = usr['nombre']
        token['apellido'] = usr['apellido']
        token['dni'] = usr['dni']

        cls.redis_assistance.hmset('token_{}'.format(h), token)
        return h


    @classmethod
    def telegram_activate(cls, codigo, token):
        k = 't_auth_{}'.format(codigo)
        if not cls.redis_assistance.hexists(k,'chat_id'):
            raise Exception('código incorrecto')

        uid = token['sub']
        cid = cls.redis_assistance.hget(k,'chat_id')
        k2 = 't_chat_id_{}'.format(cid)
        cls.redis_assistance.hset(k2,'uid',uid)

        k3 = 'telegram_{}'.format(uid)
        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        cls.redis_assistance.hmset(k3,{
            'u_nombre': usr['nombre'],
            'u_apellido': usr['apellido'],
            'u_dni': usr['dni'],
            't_chat_id': cid
        })

        cls.redis_assistance.sadd('t_authorized', uid)

    @classmethod
    def _obtener_uids_con_designacion(cls):
        query = cls.sileg_url + '/designaciones'
        r = cls.api.get(query)
        desig = r.json()
        uids = set([d["usuario_id"] for d in desig if "usuario_id" in d])
        return uids

    @classmethod
    def _obtenerHorarioHelper(cls, session, uid, fecha):
        h = cls.horario(session, uid, fecha)
        return h['horarios'][0] if h else None

    @classmethod
    def perfil(cls, session, uid, fecha, tzone='America/Argentina/Buenos_Aires'):
        assert uid is not None
        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        if not usr:
            raise Exception('usuario no encontrado {}'.format(uid))
        r = Reporte.generarReporte(session, usr, fecha, fecha, cls._obtenerHorarioHelper, tzone)

        """ transformo el reporte en info de perfil """

        reporte = r.reportes[0]
        trabajado = reporte.cantidad_segundos_trabajados
        entrada = reporte.entrada
        salida = reporte.salida
        hora_entrada = None
        hora_salida = None
        horario_segundos = 0
        if reporte.horario:
            (hora_entrada, hora_salida) = reporte.horario.obtenerInicioFin(reporte.fecha,tzone)
            horario_segundos = reporte.horario.cantidadDeSegundos()

        #proceso las justificaciones para el formato esperado:
        justificaciones = {}
        for j in reporte.justificaciones:
            if j.tipo in justificaciones:
                justificaciones[j.tipo].cantidad = justificaciones[j.tipo].cantidad + 1
            else:
                justificaciones[j.tipo] = {
                    'cantidad':1,
                    'nombre': j.nombre,
                    'descripcion': j.descripcion,
                    'codigo': j.codigo,
                    'tipo': j.tipo
                }
        ljustificaciones = [justificaciones[j] for j in justificaciones.keys()]

        #proceso los lugares de la persona.
        query = cls.sileg_url + '/usuarios/{}/designaciones'.format(uid)
        r = cls.api.get(query)
        oficinas = []
        if r.ok:
            desig = r.json()
            oficinas = [
                {
                    'id_oficina': d['lugar']['id'],
                    'oficina': d['lugar']['nombre'],
                    'cargo': d['cargo']['nombre'],
                    'tipo_cargo': d['cargo']['tipo'],
                    'desde': d['desde'],
                    'hasta': d['hasta']
                }
                for d in desig if not d['historico']
            ]

        perfil = {
            'usuario': usr,
            'fecha': reporte.fecha,
            'entrada': entrada.marcacion if entrada else None,
            'salida': salida.marcacion if salida else None,
            'segundos_trabajados': trabajado,
            'hora_entrada': hora_entrada,
            'hora_salida': hora_salida,
            'horario_segundos': horario_segundos,
            'justificaciones': ljustificaciones,
            'oficinas': oficinas
        }

        return perfil

    @classmethod
    def reporte(cls, session, uid, inicio, fin, tzone='America/Argentina/Buenos_Aires'):
        assert uid is not None
        fin = fin if fin else date.today()
        inicio = inicio if inicio else fin - timedelta(days=7)
        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        if not usr:
            return []
        return Reporte.generarReporte(session, usr, inicio, fin, cls._obtenerHorarioHelper, tzone)

    @classmethod
    def reporteJustificaciones(cls, session, uid, inicio, fin, tzone='America/Argentina/Buenos_Aires'):
        assert uid is not None
        fin = fin if fin else date.today()
        inicio = inicio if inicio else fin - timedelta(days=7)
        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        if not usr:
            return []
        return ReporteJustificaciones.generarReporte(session, usr, inicio, fin, tzone)

    @classmethod
    def reporteGeneral(cls, session, lugares, fecha, tzone='America/Argentina/Buenos_Aires'):
        ret = []
        for lid in lugares:
            # obtengo el lugar
            query = cls.sileg_url + '/lugares/' + lid
            params = {}
            r = cls.api.get(query, params)
            if not r.ok:
                lugar = None
            lugar = r.json()

            # busco los usuarios
            query = cls.sileg_url + '/designaciones/?l=' + lid
            r = cls.api.get(query)
            desig = r.json()
            logging.info(desig)
            uids = set([d["usuario_id"] for d in desig if "usuario_id" in d])
            usuarios = []
            for uid in uids:
                usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
                if not usr:
                    raise Exception('No existe el usuario con uid {}'.format(uid))
                usuarios.append(usr)

            rep = ReporteGeneral.generarReporte(session, lugar, usuarios, fecha, cls._obtenerHorarioHelper, tzone)
            ret.append(rep)

        return ret


    @classmethod
    def _localizar_fecha_a_zona(fecha, timezone):
        timezone = pytz.timezone(timezone)
        dt = datetime.combine(fecha, time(0))
        dt = timezone.localize(dt)
        return dt

    @classmethod
    def historial_horarios(cls, session, uid, fecha_inicio=None, fecha_fin=None, timezone='America/Argentina/Buenos_Aires'):
        assert uid is not None
        assert session is not None

        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        if not usr:
            raise Exception('No existe el usuario con uid {}'.format(uid))

        q = session.query(Horario).filter(Horario.usuario_id == uid)
        if fecha_inicio:
            q.filter(Horario.fecha_valido >= fecha_inicio)
        if fecha_fin:
            q.filter(Horario.fecha_valido <= fecha_fin)
        rhs = q.order_by(Horario.fecha_valido, Horario.dia_semanal).all()

        hs = {
            'usuario': usr,
            'historial': [ {'horario':h.como_dict_en_zona(timezone), 'creador':None} for h in rhs ]
        }
        return hs


    @classmethod
    def eliminar_horario(cls, session, uid, hid):
        assert uid is not None
        assert hid is not None
        h = session.query(Horario).filter(Horario.id == hid).one()
        h.eliminado = datetime.datetime.now()
        return hid

    @classmethod
    def horario(cls, session, uid, fecha):
        assert uid is not None
        fecha = fecha if fecha else date.today()

        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        if not usr:
            raise Exception('No existe el usuario con uid {}'.format(uid))

        horarios = []
        hsSemanales = 0

        for i in range(0, 7):
            actual = fecha + timedelta(days=i)

            q = session.query(Horario)
            q = q.filter(Horario.usuario_id == uid, Horario.dia_semanal == actual.weekday(), Horario.fecha_valido <= actual, Horario.eliminado == None)
            q = q.order_by(Horario.fecha_valido.desc())
            horario = q.limit(1).one_or_none()

            if horario is None:
                horario = Horario()
                horario.dia_semanal = actual.weekday()
                horario.hora_entrada = 0
                horario.hora_salida = 0

            horarios.append(horario)
            hsSemanales = hsSemanales + (horario.hora_salida - horario.hora_entrada)

        minSem = (hsSemanales /60)  % 60
        hsSem = int((hsSemanales /60)  / 60)
        datos = {
                'horarios': horarios,
                'horasSemanales': {'horas': hsSem, 'minSem': minSem},
                'usuario': usr
                }
        return datos

    @classmethod
    def crearHorario(cls, session, horarios):
        for h in horarios:
            uid = h['usuario_id']
            horario = Horario()
            horario.fecha_valido = parser.parse(h['fecha_valido']).date() if h['fecha_valido'] else None
            horario.dia_semanal = h['dia_semanal']
            horario.hora_entrada = h['hora_entrada']
            horario.hora_salida = h['hora_salida']
            horario.usuario_id = uid
            horario.id = str(uuid.uuid4())
            session.add(horario)

    @classmethod
    def usuario(cls, session, uid, retornarClave=False):
        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        return {
            'usuario': usr,
            'asistencia': None
        }

    @classmethod
    def lugares(cls, session, search):
        query = cls.sileg_url + '/lugares/'
        params = {}
        if search:
            params['q'] = search

        logging.debug(query)
        r = cls.api.get(query, params)
        if not r.ok:
            return []

        return r.json()

    @classmethod
    def usuarios_search(cls, session, search):
        query = cls.sileg_url + '/usuarios'
        r = cls.api.get(query)
        if not r.ok:
            raise Exception()
        
        usuarios = r.json()
        uids = set([u['usuario'] for u in usuarios])

        tk = cls.api._get_token()
        usuarios = cls.cache_usuarios.obtener_usuarios_por_uids(uids,tk)

        ''' mejoro un poco el texto de search para que matchee la cadena de nombre apellido dni'''
        rsearch = '.*{}.*'.format(search.replace('.','').replace(' ', '.*'))
        r = re.compile(rsearch, re.I)
        filtrados = [u for u in usuarios if r.match(u['nombre'] + ' ' + u['apellido'] + ' ' + u['dni'])]
        return filtrados        


    @classmethod
    def sub_usuarios_search(cls, session, uid, search):
        query = cls.sileg_url + '/usuarios/{}/subusuarios'.format(uid)
        r = cls.api.get(query)
        if not r.ok:
            raise Exception()
        
        usuarios = r.json()
        uids = set([u['usuario'] for u in usuarios])

        tk = cls.api._get_token()
        usuarios = [cls.cache_usuarios.obtener_usuario_por_uid(uid,tk) for uid in uids]

        ''' mejoro un poco el texto de search para que matchee la cadena de nombre apellido dni'''
        rsearch = '.*{}.*'.format(search.replace('.','').replace(' ', '.*'))
        r = re.compile(rsearch, re.I)
        filtrados = [ u for u in usuarios if r.match(u['nombre'] + ' ' + u['apellido'] + ' ' + u['dni'])]
        return filtrados


    '''
        APIs de justificaciones
    '''

    @classmethod
    def justificaciones(cls, session):
        return session.query(Justificacion).filter(Justificacion.eliminado == None).all()


    @classmethod
    def justificacion(cls, session, jid):
        return session.query(Justificacion).filter(Justificacion.id == jid).one()

    @classmethod
    def crear_justificacion(cls, session, justificacion):
        q = session.query(Justificacion).filter(or_(Justificacion.nombre == justificacion["nombre"], Justificacion.codigo == justificacion["codigo"]))
        q = q.filter(Justificacion.eliminado == None)
        if q.count() > 0:
            raise Exception('Justificacion existente')

        j = Justificacion()
        j.id = str(uuid.uuid4())
        j.nombre = justificacion["nombre"]
        j.descripcion = justificacion["descripcion"] if "descripcion" in justificacion else None
        j.codigo = justificacion["codigo"]
        j.general = justificacion["general"]

        session.add(j)
        return j.id

    @classmethod
    def eliminarJustificacion(cls, session, jid):
        justificacion = session.query(Justificacion).filter(Justificacion.id == jid).one()
        justificacion.eliminado = datetime.datetime.now()

    @classmethod
    def eliminarFechaJustificada(cls, session, jid, autorizador_id=None):

        justificacion = session.query(FechaJustificada).filter(FechaJustificada.id == jid).one()
        logging.info(justificacion)
        justificacion.eliminado = datetime.datetime.now()
        if not autorizador_id:
            autorizador_id = justificacion.usuario_id
        justificacion.autorizador_id = autorizador_id

        """
            ver como analizar estos casos para manejarlo mas genéricamente
        """
        if justificacion.justificacion.id == CompensatoriosModel.JUSTIFICACION:
            cantidad = 1

            if justificacion.fecha_fin:
                cantidad = (justificacion.fecha_fin - justificacion.fecha_inicio).days + 1
            notas = 'Compensatorio Cancelado {}'.format(justificacion.fecha_inicio.date())
            CompensatoriosModel.cambiarSaldo(session, autorizador_id, justificacion.usuario_id, cantidad, notas)


        return justificacion.id

    @classmethod
    def actualizar_justificacion(cls, session, jid, datos):
        justificacion = session.query(Justificacion).filter(Justificacion.id == jid).one()
        justificacion.nombre = datos["nombre"]
        justificacion.descripcion = datos["descripcion"]
        justificacion.codigo = datos["codigo"]
        justificacion.general = datos["general"]


    @classmethod
    def justificar(cls, session, fj, autorizador_id=None):
        fj["fecha_inicio"] = parser.parse(fj["fecha_inicio"]) if fj["fecha_inicio"] else None
        if fj["fecha_inicio"] is None:
            raise Exception("Debe poseer fecha de inicio")

        fj["fecha_fin"] = parser.parse(fj["fecha_fin"]) if fj["fecha_fin"] else None

        if not autorizador_id:
            autorizador_id = fj['usuario_id']

        just = fj["justificacion"]
        j = FechaJustificada()
        j.id = str(uuid.uuid4())
        j.fecha_inicio = fj["fecha_inicio"]
        j.fecha_fin = fj["fecha_fin"]
        j.usuario_id = fj["usuario_id"] if 'usuario_id' in fj else None
        j.justificacion_id = just["id"]
        j.autorizador_id = autorizador_id
        session.add(j)

        """
            ver como analizar estos casos para manejarlo mas genéricamente
        """
        if just['id'] == CompensatoriosModel.JUSTIFICACION:
            cantidad = -1
            if fj['fecha_fin']:
                cantidad = ((fj['fecha_fin'] - fj['fecha_inicio']).days + 1) * -1
            fecha_notas = fj['fecha_inicio'].date()
            notas = 'Compensatorio Tomado {}'.format(fecha_notas)
            CompensatoriosModel.cambiarSaldo(session, autorizador_id, fj['usuario_id'], cantidad, notas)

        return j.id


    """
        /////////////////////////////////////////////////////////////////
                        APIS DE JUSTIFICCACIONES
        //////////////////////////////////////////////
    """

    '''
        APIs de compensatorios
    '''
    '''
        export class DatosCompensatorio
            compensatorios:  Array<Compensatorio>;
            cantidad: number;
            usuario: Usuario;

        export class Compensatorio
            registro_id: string;
            fecha: Date = null;
            notas: string = null;
            autorizador_id: string;
            cantidad: number;
    '''

    @classmethod
    def compensatorios(cls, session, uid):  
        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        if not usr:
            raise Exception('usuario no encontrado {}'.format(uid))

        datos_saldo = CompensatoriosModel.obtenerSaldo(session, uid)
        datos_compensatorios = [ 
            {
                'creado': a['asiento'].fecha,
                'cantidad': a['registros'][0].cantidad,
                'notas': a['asiento'].notas,
                'autorizador': cls.cache_usuarios.obtener_usuario_por_uid(a['asiento'].autorizador_id)
            }
            for a in datos_saldo['asientos']
        ]
        r = {
            'compensatorios': datos_compensatorios,
            'cantidad': datos_saldo['saldo'],
            'usuario': usr
        }
        return r

    @classmethod
    def crear_compensatorio(cls, session, compensatorio, id_creador_compensatorio):
        uid = compensatorio['usuario_id']
        notas = compensatorio['notas']
        cantidad = int(compensatorio['cantidad'])
        aid = CompensatoriosModel.cambiarSaldo(session, id_creador_compensatorio, uid, cantidad, notas)
        return aid


    '''
        APIs de los relojes
    '''

    @classmethod
    def relojes(cls, session):
        return session.query(Reloj).all()

    @classmethod
    def reloj(cls, session, rid):
        return session.query(Reloj).filter(Reloj.id == rid).one()

    @classmethod
    def usuarios_por_reloj(cls, session, rid):
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zk = {'reloj':reloj, 'api':ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=reloj.zona_horaria)}
        return zk['api'].getUserInfo()

    @classmethod
    def usuario_por_reloj(cls, session, rid, ruid):
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zk = {'reloj':reloj, 'api':ZkSoftware( host=reloj.ip, port=reloj.puerto, timezone=reloj.zona_horaria)}
        return zk['api'].getUserInfo(ruid)

    @classmethod
    def templates_por_reloj(cls, session, rid):
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zk = {'reloj':reloj, 'api':ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=reloj.zona_horaria)}
        return zk['api'].getUserTemplate()

    @classmethod
    def templates_por_usuario_por_reloj(cls, session, rid, ruid):
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zk = {'reloj':reloj, 'api':ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=reloj.zona_horaria)}
        r = zk['api'].getUserTemplate(ruid)
        if type(r) != list:
            return [r]
        else:
            return r

    @classmethod
    def eliminar_huellas_reloj(cls, session, rid):
        ''' debo verificar que las huellas a eliminar existan en la base del sistema!!! '''
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zk = {'reloj':reloj, 'api':ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=reloj.zona_horaria)}
        #r = zk['api'].clearTemplates()
        #return r
        return {}

    @classmethod
    def eliminar_usuarios_reloj(cls, session, rid):
        ''' debo verificar que los usuarios a eliminar existan en la base del sistema!!! '''
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zk = {'reloj':reloj, 'api':ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=reloj.zona_horaria)}
        #r = zk['api'].clearUsers()
        #return r
        return {}

    @classmethod
    def marcaciones_por_reloj(cls, session, rid):
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zk = {'reloj':reloj, 'api':ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=reloj.zona_horaria)}
        return zk['api'].getAttLog()

    @classmethod
    def sincronizar(cls, session):
        q = session.query(Reloj.id).filter(Reloj.activo).all()
        sincronizados = []
        for rid in q:
            sincronizados.extend(cls.sincronizar_reloj(session, rid))
        return sincronizados

    @classmethod
    def _publicar_en_redis(cls, dni, usuario, marcacion):
        from rest_utils import ApiJSONEncoder
        m = {
            'dni': dni,
            'usuario': usuario,
            'log': marcacion
        }
        m2 = json.dumps(m, cls=ApiJSONEncoder)
        logger.info('enviando a redis {}'.format(m2))
        cls.redis_assistance.sadd('telegram', m2)
        #cls.redis_assistance.sadd('correos', m2)

    @classmethod
    def sincronizar_reloj(cls, session, rid):
        logger = logging.getLogger('assistance.model.zkSoftware')

        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zona_horaria = reloj.zona_horaria
        if not zona_horaria:
            zona_horaria = 'America/Argentina/Buenos_Aires'
        zk = {'reloj':reloj, 'api':ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=zona_horaria)}
        logs = zk['api'].getAttLog()
        if len(logs) <= 0:
            yield

        token = cls.api._get_token()
        try:
            for l in logs:
                dni = l['PIN'].strip().lower()
                usuario = cls.usuarios_cache.obtener_usuario_por_dni(dni, token=token)
                marcacion = l['DateTime']

                ms = session.query(Marcacion).filter(and_(Marcacion.usuario_id == usuario['id'], Marcacion.marcacion == marcacion)).all()
                if len(ms) <= 0:
                    log = Marcacion()
                    log.id = str(uuid.uuid4())
                    log.usuario_id = usuario['id']
                    log.dispositivo_id = zk['reloj'].id
                    log.tipo = l['Verified']
                    log.marcacion = marcacion
                    session.add(log)
                    r = {'estado':'agregada', 'marcacion':log, 'dni':dni, 'nombre':usuario['nombre'], 'apellido':usuario['apellido']}
                    logger.info(r)

                    try:
                        cls._publicar_en_redis(dni, usuario, log)
                    except Exception as e:
                        logger.exception(e)


                    yield r
                else:

                    """
                    try:
                        cls._publicar_en_redis(dni, usuario, m)
                    except Exception as e:
                        logger.exception(e)
                    """
                    
                    for m in ms:
                        yield {'estado':'existente', 'marcacion':m, 'dni':dni}
                        logger.warn('Marcación duplicada {} {} {}'.format(usuario['id'], dni, marcacion))

            if cls.eliminar_logs_relojes:
                logs2 = zk['api'].getAttLog()
                if len(logs) > 0 and len(logs2) == len(logs):
                    zk['api'].clearAttLogs()
                    yield {'estado':'borrando_logs', 'mensaje':'eliminando {} logs'.format(len(logs2))}


        except Exception as e:
            logger.exception(e)
            yield {'estado':'error', 'mensaje':str(e)}
            raise e
