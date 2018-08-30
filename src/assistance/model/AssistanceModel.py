from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, with_polymorphic
from datetime import datetime, date, timedelta
import requests
import os
import uuid
from dateutil import parser
import datetime

import logging
from logging.handlers import TimedRotatingFileHandler
logger = logging.getLogger('assistance.model.zkSoftware')
hdlr = TimedRotatingFileHandler('/var/log/assistance/sinc_logs.log', when='D', interval=1)
formatter = logging.Formatter('%(asctime)s, %(name)s, %(module)s, %(filename)s, %(funcName)s, %(levelname)s, %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)


import oidc
from oidc.oidc import ClientCredentialsGrant

from assistance.model.zkSoftware import ZkSoftware
from .entities import *

import json
import redis
REDIS_HOST = os.environ.get('TELEGRAM_BOT_REDIS')
REDIS_PORT = int(os.environ.get('TELEGRAM_BOT_REDIS_PORT', 6379))
VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))

class AssistanceModel:

    verify = VERIFY_SSL
    usuarios_url = os.environ['USERS_API_URL']
    sileg_url = os.environ['SILEG_API_URL']
    client_id = os.environ['OIDC_CLIENT_ID']
    client_secret = os.environ['OIDC_CLIENT_SECRET']

    redis_assistance = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    @classmethod
    def _get_token(cls):
        ''' obtengo un token mediante el flujo client_credentials para poder llamar a la api de usuarios '''
        grant = ClientCredentialsGrant(cls.client_id, cls.client_secret, verify=cls.verify)
        token = grant.get_token(grant.access_token())
        if not token:
            raise Exception()
        return token

    @classmethod
    def api(cls, api, params=None, token=None):
        if not token:
            token = cls._get_token()

        ''' se deben cheqeuar intentos de login, y disparar : SeguridadError en el caso de que se haya alcanzado el máximo de intentos '''
        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        logging.debug(api)
        logging.debug(params)
        r = requests.get(api, verify=cls.verify, headers=headers, params=params)
        logging.debug(r)
        return r

    @classmethod
    def api_post(cls, api, data=None, token=None):
        if not token:
            token = cls._get_token()

        ''' se deben cheqeuar intentos de login, y disparar : SeguridadError en el caso de que se haya alcanzado el máximo de intentos '''
        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        logging.debug(api)
        logging.debug(data)
        r = requests.post(api, verify=cls.verify, headers=headers, json=data)
        logging.debug(r)
        return r

    @classmethod
    def api_delete(cls, api, token=None):
        if not token:
            token = cls._get_token()

        ''' se deben cheqeuar intentos de login, y disparar : SeguridadError en el caso de que se haya alcanzado el máximo de intentos '''
        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        logging.debug(api)
        r = requests.delete(api, verify=cls.verify, headers=headers)
        logging.debug(r)
        return r

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
    def _setear_usuario_cache(cls, usr):
        cls.redis_assistance.hmset('usuario_uid_{}'.format(usr['id']), usr)
        cls.redis_assistance.hset('usuario_dni_{}'.format(usr['dni'].lower().replace(' ','')), 'uid', usr['id'])

    @classmethod
    def _obtener_usuario_por_uid(cls, uid, token=None):
        usr = cls.redis_assistance.hgetall('usuario_uid_{}'.format(uid))
        if len(usr.keys()) > 0:
            return usr
        
        query = cls.usuarios_url + '/usuarios/' + uid
        r = cls.api(query, token=token)
        if not r.ok:
            return []
        usr = r.json()
        cls._setear_usuario_cache(usr)
        return usr
    
    @classmethod
    def _obtener_usuario_por_dni(cls, dni, token=None):
        key = 'usuario_dni_{}'.format(dni.lower().replace(' ',''))
        if cls.redis_assistance.hexists(key,'uid'):
            uid = cls.redis_assistance.hget(key,'uid')
            return cls._obtener_usuario_por_uid(uid, token)

        query = cls.usuarios_url + '/usuarios/'
        params = {}
        params['c'] = True
        params = {'q':dni}
        r = cls.api(query, params=params, token=token)
        if not r.ok:
            raise Exception(r.text)
        for jusr in r.json():
            usr = json.loads(jusr)
            cls._setear_usuario_cache(usr)
            return usr
        raise Exception('No se encuentra usuario con dni {}'.format(dni))

    """
    /////////////////////////////
    """

    @classmethod
    def _obtener_uids_con_designacion(cls):
        query = cls.sileg_url + '/designaciones'
        r = cls.api(query)
        desig = r.json()
        uids = set([d["usuario_id"] for d in desig if "usuario_id" in d])
        return uids


    @classmethod
    def perfil(cls, session, uid, fecha, tzone='America/Argentina/Buenos_Aires'):
        assert uid is not None
        usr = cls._obtener_usuario_por_uid(uid)
        r = Reporte.generarReporte(session, usr, fecha, fecha, tzone)

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
        r = cls.api(query)
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
        usr = cls._obtener_usuario_por_uid(uid)
        if not usr:
            return []
        return Reporte.generarReporte(session, usr, inicio, fin, tzone)

    @classmethod
    def reporteGeneral(cls, session, lugares, fecha, tzone='America/Argentina/Buenos_Aires'):
        ret = []
        for lid in lugares:
            # obtengo el lugar
            query = cls.sileg_url + '/lugares/' + lid
            params = {}
            r = cls.api(query, params)
            if not r.ok:
                lugar = None
            lugar = r.json()

            # busco los usuarios
            query = cls.sileg_url + '/designaciones/?l=' + lid
            r = cls.api(query)
            desig = r.json()
            logging.info(desig)
            uids = set([d["usuario_id"] for d in desig if "usuario_id" in d])
            usuarios = []
            for uid in uids:
                usr = cls._obtener_usuario_por_uid(uid)
                if not usr:
                    raise Exception('No existe el usuario con uid {}'.format(uid))
                usuarios.append(usr)

            rep = ReporteGeneral.generarReporte(session, lugar, usuarios, fecha, tzone)
            ret.append(rep)

        return ret

    @classmethod
    def historial_horarios(cls, session, uid, fecha_inicio=None, fecha_fin=None):
        assert uid is not None
        assert session is not None

        usr = cls._obtener_usuario_por_uid(uid)
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
            'historial': [ {'horario':h, 'creador':None} for h in rhs ]
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

        usr = cls._obtener_usuario_por_uid(uid)
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
        usr = cls._obtener_usuario_por_uid(uid)
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
        r = cls.api(query, params)
        if not r.ok:
            return []

        return r.json()

    @classmethod
    def usuarios(cls, session, search, retornarClave, offset, limit, fecha):

        query = cls.usuarios_url + '/usuarios/'
        params = {}
        if retornarClave:
            params['c'] = True
        params = {'q':search}
        r = cls.api(query,params=params)
        if not r.ok:
            raise Exception(r.text)

        uids = cls._obtener_uids_con_designacion()

        usuarios = []
        for usr in r.json():
            cls._setear_usuario_cache(usr)
            usuarios.append({
                    'usuario':usr,
                    'asistencia': usr if usr['id'] in uids else None
                })
        return usuarios

        """
        import re
        r = '^.*{}.*$'.format(search.replace(' ','.*'))
        reg = re.compile(r)

        usuarios = []
        uids = cls._obtener_uids_con_designacion()
        token = cls._get_token()
        for uid in uids:
            usr = cls._obtener_usuario_por_uid(uid, token)
            if search:
                fn = usr['nombre'] + ' ' + usr['apellido']
                if reg.match(fn):
                    usuarios.append({
                            'usuario':usr,
                            'asistencia':None
                        })

        return usuarios
        """




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
    def eliminarFechaJustificada(cls, session, jid):
        justificacion = session.query(FechaJustificada).filter(FechaJustificada.id == jid).one()
        logging.info(justificacion)
        justificacion.eliminado = datetime.datetime.now()
        return justificacion.id

    @classmethod
    def actualizar_justificacion(cls, session, jid, datos):
        justificacion = session.query(Justificacion).filter(Justificacion.id == jid).one()
        justificacion.nombre = datos["nombre"]
        justificacion.descripcion = datos["descripcion"]
        justificacion.codigo = datos["codigo"]
        justificacion.general = datos["general"]


    @classmethod
    def justificar(cls, session, fj):
        fj["fecha_inicio"] = parser.parse(fj["fecha_inicio"]) if fj["fecha_inicio"] else None
        if fj["fecha_inicio"] is None:
            raise Exception("Debe poseer fecha de inicio")

        fj["fecha_fin"] = parser.parse(fj["fecha_fin"]) if fj["fecha_fin"] else None

        just = fj["justificacion"]
        j = FechaJustificada()
        j.id = str(uuid.uuid4())
        j.fecha_inicio = fj["fecha_inicio"]
        j.fecha_fin = fj["fecha_fin"]
        j.usuario_id = fj["usuario_id"] if 'usuario_id' in fj else None
        j.justificacion_id = just["id"]

        session.add(j)
        return j.id

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

        token = cls._get_token()
        try:
            for l in logs:
                dni = l['PIN'].strip().lower()
                usuario = cls._obtener_usuario_por_dni(dni, token=token)
                marcacion = l['DateTime']

                m = session.query(Marcacion).filter(and_(Marcacion.usuario_id == usuario['id'], Marcacion.marcacion == marcacion)).one_or_none()
                if not m:
                    log = Marcacion()
                    log.id = str(uuid.uuid4())
                    log.usuario_id = usuario['id']
                    log.dispositivo_id = zk['reloj'].id
                    log.tipo = l['Verified']
                    log.marcacion = marcacion
                    session.add(log)
                    r = {'estado':'agregada', 'marcacion':log, 'dni':dni}
                    logger.info(r)

                    try:
                        from rest_utils import ApiJSONEncoder
                        m = {
                            'dni':dni,
                            'usuario_id': usuario['id'],
                            'usuario': usuario,
                            'log':log
                        }
                        m2 = json.dumps(m, cls=ApiJSONEncoder)
                        logger.info('enviando a redis {}'.format(m2))
                        cls.redis_assistance.sadd('marcaciones', m2)
                    except Exception as e:
                        logger.exception(e)


                    yield r
                else:
                    yield {'estado':'existente', 'marcacion':m, 'dni':dni}
                    logger.warn('Marcación duplicada {} {} {}'.format(usuario.id, dni, marcacion))

            logs2 = zk['api'].getAttLog()
            if len(logs) > 0 and len(logs2) == len(logs):
                zk['api'].clearAttLogs()
                yield {'estado':'borrando_logs', 'mensaje':'eliminando {} logs'.format(len(logs2))}


        except Exception as e:
            logger.exception(e)
            yield {'estado':'error', 'mensaje':str(e)}
            raise e
