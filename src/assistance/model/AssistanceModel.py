from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, with_polymorphic
from datetime import datetime, date, timedelta
import pytz
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
from .RelojesModel import RelojesModel

from .LugaresCache import LugaresCache, LugaresAPI, LugaresGetters
from .CargosCache import CargosCache, CargosAPI, CargosGetters
from .entities import *
from .AsientosModel import CompensatoriosModel

import json
import redis
REDIS_HOST = os.environ.get('TELEGRAM_BOT_REDIS')
REDIS_PORT = int(os.environ.get('TELEGRAM_BOT_REDIS_PORT', 6379))
VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))

MONGO_URL = os.environ['MONGO_URL']
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
_LUGARES_API = LugaresAPI(api_url=SILEG_API, api=_API)
_LUGARES_GETTER = LugaresGetters(_LUGARES_API)

_CARGOS_API = CargosAPI(api_url=SILEG_API, api=_API)
_CARGOS_GETTER = CargosGetters(_CARGOS_API)

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

    cache_lugares = LugaresCache(mongo_url=MONGO_URL,
                                 getters=_LUGARES_GETTER, timeout=60 * 60)

    cache_cargos = CargosCache(mongo_url=MONGO_URL,
                                getters=_CARGOS_GETTER, timeout=60 * 60)
   

    @classmethod
    def _config(cls):
        volumen = os.environ['VOLUMEN_CONFIG']
        with open(volumen + '/config.json','r') as f:
            config = json.load(f)
        return config

    @classmethod
    def _obtener_nivel_maximo(cls, uid, cargos):
        """ filtro los usuarios que podría ver de acuerdo a su cargo (solo los que tienen nivel mas alto) """
        mismo = [u for u in cargos if u['usuario'] == uid]
        maximo = 100
        if mismo and len(mismo) > 0:
            for c in mismo:
                if maximo > c['cargo_nivel']:
                    maximo = c['cargo_nivel']        
        return maximo

    @classmethod
    def _obtener_subusuarios(cls, uid):
        usuarios_cargo = []
        lids = cls.cache_lugares.obtener_lugares_por_usuario_id(uid)
        for lid in lids:
            usrs = cls.cache_lugares.obtener_subusuarios_por_lugar_id(lid)
            usuarios_cargo.extend(usrs)

        nivel = cls._obtener_nivel_maximo(uid, usuarios_cargo)
        filtrados = [u for u in usuarios_cargo if u['cargo_nivel'] > nivel]
        return filtrados

    @classmethod
    def chequear_acceso(cls, caller_id, uid):
        """
            chequea si un usuario tiene acceso a los datos de otro usuario
        """
        assert caller_id is not None
        assert uid is not None
        if caller_id == uid:
            return True
        usuarios_cargo = cls._obtener_subusuarios(caller_id)
        uids = [u['usuario'] for u in usuarios_cargo]
        ok = uid in uids
        return ok

    @classmethod
    def chequear_acceso_lugares(cls, caller_id, lugares=[]):
        lids = cls.cache_lugares.obtener_lugares_por_usuario_id(caller_id)
        acumulador = []
        acumulador.extend(lids)
        for lid in lids:
            slids = cls.cache_lugares.obtener_sublugares_por_lugar_id(lid)
            acumulador.extend(slids)
        usuario_lugares = set(acumulador)
        lugares_pedidos = set(lugares)
        return lugares_pedidos.issubset(usuario_lugares)

    @classmethod
    def obtener_acceso_modulos(cls, uid):
        """
            si tiene subusuarios entonces retorna las funciones del perfil default-authority
        """
        uids = cls._obtener_subusuarios(uid)
        if not uid or len(uids) <= 0:
            return None
        config = cls._config()
        pgen = (p for p in config['api']['perfiles'] if p['perfil'] == 'default-authority')
        perfil = next(pgen)
        if not perfil:
            raise Exception('no se encontró el perfil default-authority')
        return perfil['funciones']


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
    def _procesar_justificacion_reporte(cls, j):
        r = j.__json__()
        if j.creador_id:
            r['creador'] = cls.cache_usuarios.obtener_usuario_por_uid(j.creador_id)
        if j.actualizador_id:
            r['actualizador'] = cls.cache_usuarios.obtener_usuario_por_uid(j.actualizador_id)
        if j.eliminador_id:
            r['eliminador'] = cls.cache_usuarios.obtener_usuario_por_uid(j.eliminador_id)
        return r

    @classmethod
    def reporteJustificaciones(cls, session, uid, inicio, fin, tzone='America/Argentina/Buenos_Aires'):
        assert uid is not None
        fin = fin if fin else date.today()
        inicio = inicio if inicio else fin - timedelta(days=7)
        usr = cls.cache_usuarios.obtener_usuario_por_uid(uid)
        if not usr:
            return []
        reporte = ReporteJustificaciones.generarReporte(session, usr, inicio, fin, tzone)

        '''
            agrego el usuario a las justificaciones para la visual del reporte
        '''
        reporte.justificaciones = [cls._procesar_justificacion_reporte(j) for j in reporte.justificaciones]
        reporte.justificaciones_eliminadas = [cls._procesar_justificacion_reporte(j) for j in reporte.justificaciones_eliminadas]

        return reporte

    @classmethod
    def _buscar_lugar_en_arbol(cls, lid, arbol):
        if arbol['lugar'] == lid:
            return True
        for h in arbol['hijos']:
            if cls._buscar_lugar_en_arbol(lid, h):
                return True
        return False

    @classmethod
    def reporteGeneralAdmin(cls, session, lugares, fecha, tzone='America/Argentina/Buenos_Aires'):
        ret = []
        for lid in lugares:
            usuarios_cargos = cls.cache_lugares.obtener_subusuarios_por_lugar_id(lid)
            uids = [u['usuario'] for u in usuarios_cargos]
            usuarios = cls.cache_usuarios.obtener_usuarios_por_uids(uids)
            lugar = cls.cache_lugares.obtener_lugar_por_id(lid)

            ''' genero el reporte para el lugar '''
            rep = ReporteGeneral.generarReporte(session, lugar, usuarios, fecha, cls._obtenerHorarioHelper, tzone)
            ret.append(rep)
        return ret

    @classmethod
    def reporteGeneral(cls, session, authorized_id, lugares, fecha, tzone='America/Argentina/Buenos_Aires'):
        ret = []

        """ busco los arboles de los lugares con los cargos """
        arboles = []
        tk = _API._get_token()
        for lid in lugares:
            arbol = cls.cache_lugares.obtener_arbol_por_lugar_id(lid, tk)
            if arbol:
                arboles.append(arbol)

        ''' agrego los lugars donde la persona tiene cargo. asi estoy seguro de encontrar el nivel por cada subarbol '''
        lugares_con_cargo = cls.cache_lugares.obtener_lugares_por_usuario_id(authorized_id, tk)
        for lid in lugares_con_cargo:
            if lid not in lugares:
                arbol = cls.cache_lugares.obtener_arbol_por_lugar_id(lid, tk)
                if arbol:
                    arboles.append(arbol)

        for lid in lugares:
            ''' busco el arbol de profundiad máxima que contenga lid (necesario para obtener el cargo de authorized_id ya que esta en la raiz)'''
            raices = [a for a in arboles if cls._buscar_lugar_en_arbol(lid, a)]
            raices.sort(key=lambda n: n['profundidad'], reverse=True)
            maximo = raices[0]

            ''' obtengo el cargo que contiene en el arbol '''
            usuarios_cargos = maximo['usuarios']
            nivel = cls._obtener_nivel_maximo(authorized_id, usuarios_cargos)

            ''' obtengo los usuarios que tienen cargos mas bajos '''
            usuarios_cargos = cls.cache_lugares.obtener_subusuarios_por_lugar_id(lid)
            uids = [u['usuario'] for u in usuarios_cargos if 'cargo_nivel' in u and u['cargo_nivel'] and u['cargo_nivel'] > nivel]
            usuarios = cls.cache_usuarios.obtener_usuarios_por_uids(uids)
            lugar = cls.cache_lugares.obtener_lugar_por_id(lid)

            ''' genero el reporte para el lugar '''
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
        }

    @classmethod
    def sublugares_por_lugar_id(cls, lugar_id, search=''):
        tk = cls.api._get_token()
        lids = cls.cache_lugares.obtener_sublugares_por_lugar_id(lugar_id, tk)
        if not lids:
            return []
        lugares = []
        for lid in lids:
            lugar = cls.cache_lugares.obtener_lugar_por_id(lid, tk)
            lugares.append(lugar)

        ''' mejoro un poco el texto de search para que matchee la cadena de nombre apellido dni'''
        rsearch = '.*{}.*'.format(search.replace('.','').replace(' ', '.*'))
        r = re.compile(rsearch, re.I)
        filtrados = [ l for l in lugares if r.match(l['nombre'])]
        return filtrados

    @classmethod
    def lugares(cls, session, autorizador_id, search=''):
        lugares = []
        padres_lids = cls.cache_lugares.obtener_lugares_por_usuario_id(autorizador_id)
        if not padres_lids or len(padres_lids) <= 0:
            return []
        lids = []
        lids.extend(padres_lids)
        for lid in padres_lids:
            alids = cls.cache_lugares.obtener_sublugares_por_lugar_id(lid)
            lids.extend(alids)

        tk = _API._get_token()
        for lid in lids:
            lugar = cls.cache_lugares.obtener_lugar_por_id(lid, tk)
            if lugar:
                lugares.append(lugar)

        ''' mejoro un poco el texto de search para que matchee la cadena de nombre apellido dni'''
        rsearch = '.*{}.*'.format(search.replace('.','').replace(' ', '.*'))
        r = re.compile(rsearch, re.I)
        filtrados = [ l for l in lugares if r.match(l['nombre'])]
        return filtrados

    """
    esta implementación busca en todas las designaciones!!
    algo mas eficiente es buscar sobre las designaciones del lugar raiz de la config. 
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
    """
    
    @classmethod
    def usuarios_search(cls, search):
        config = cls._config()
        lid = config['api']['lugar_raiz']
        usuarios_cargo = cls.cache_lugares.obtener_subusuarios_por_lugar_id(lid)
        uids = list(set((u['usuario'] for u in usuarios_cargo)))
        usuarios = cls.cache_usuarios.obtener_usuarios_por_uids(uids)

        ''' mejoro un poco el texto de search para que matchee la cadena de nombre apellido dni'''
        rsearch = '.*{}.*'.format(search.replace('.','').replace(' ', '.*'))
        r = re.compile(rsearch, re.I)
        filtrados = [ u for u in usuarios if r.match(u['nombre'] + ' ' + u['apellido'] + ' ' + u['dni'])]
        return filtrados

    @classmethod
    def sub_usuarios_search(cls, uid, search):
        usuarios_cargo = cls._obtener_subusuarios(uid)
        uids = list(set((u['usuario'] for u in usuarios_cargo)))
        usuarios = cls.cache_usuarios.obtener_usuarios_por_uids(uids)

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


    """
        //////////////// manejar las justificaciones para determinados cargos /////////////////
    """

    @classmethod
    def _es_planta(cls, cargo):
        r = re.compile(r'.*?\w\d\d.*')
        if r.match(cargo['nombre']):
            return True
        return False

    @classmethod
    def _es_contrato(cls, cargo):
        r = re.compile(r'.*Contrato.*')
        if r.match(cargo['nombre']):
            return True
        return False

    @classmethod
    def _es_beca(cls, cargo):
        r = re.compile(r'.*Beca.*')
        if r.match(cargo['nombre']):
            return True
        return False

    @classmethod
    def justificacionesParaUsuario(cls, session, uid):
        designaciones = cls.cache_cargos.obtener_cargos_por_usuario_id(uid)
        cargos_no_docentes = [c['cargo'] for c in designaciones if 'No Docente' in c['cargo']['tipo']]
        if len(cargos_no_docentes) <= 0:
            return []

        just = session.query(Justificacion).filter(Justificacion.eliminado == None).all()

        aa = 'e0dfcef6-98bb-4624-ae6c-960657a9a741'
        compensatorio = '48773fd7-8502-4079-8ad5-963618abe725'
        bs = 'fa64fdbd-31b0-42ab-af83-818b3cbecf46'
        a102 = '4d7bf1d4-9e17-4b95-94ba-4ca81117a4fb'
        pe = 'b70013e3-389a-46d4-8b98-8e4ab75335d0'

        todos = set([aa, compensatorio, bs])
        planta = set([a102, pe]).union(todos)
        becas = set([pe]).union(todos)

        conjunto = set().union(todos)
        for c in cargos_no_docentes:
            if cls._es_planta(c):
                conjunto = conjunto.union(planta)
            if cls._es_beca(c):
                conjunto = conjunto.union(becas)

        justificaciones = [j for j in just if j.id in conjunto]
        return justificaciones


    @classmethod
    def reporte_justificaciones_realizadas(cls, session, cantidad=10):

        def _obtener_oficinas(uid,token):
            cargos = cls.cache_cargos.obtener_cargos_por_usuario_id(uid,token)
            acc = []
            for c in cargos:
                if not c['historico']:
                    #oficina = f"{c['lugar']['nombre']} {c['cargo']['nombre']}"
                    oficina = c['lugar']['nombre']
                    if oficina not in acc:
                        acc.append(oficina)
            return acc

        justificaciones = []
        token = cls.api._get_token()
        for j in session.query(FechaJustificada).order_by(FechaJustificada.fecha_inicio.desc()).limit(cantidad).options(joinedload('justificacion')).all():
            r = j.__json__()
            c = cls.cache_usuarios.obtener_usuario_por_uid(j.usuario_id, token=token) if j.usuario_id else None
            if c:
                r['usuario'] = {
                    'nombre': c['nombre'],
                    'apellido': c['apellido'],
                    'dni': c['dni'],
                    'oficinas': _obtener_oficinas(c['id'],token)
                }
            c = cls.cache_usuarios.obtener_usuario_por_uid(j.creador_id, token=token) if j.creador_id else None
            if c:
                r['creador'] = {
                    'nombre': c['nombre'],
                    'apellido': c['apellido'],
                    'dni': c['dni'],
                    'oficinas': _obtener_oficinas(c['id'],token)
                }
            c = cls.cache_usuarios.obtener_usuario_por_uid(j.actualizador_id, token=token) if j.actualizador_id else None
            if c:
                r['actualizador'] = {
                    'nombre': c['nombre'],
                    'apellido': c['apellido'],
                    'dni': c['dni'],
                    'oficinas': _obtener_oficinas(c['id'],token)
                }
            c = cls.cache_usuarios.obtener_usuario_por_uid(j.eliminador_id, token=token) if j.eliminador_id else None
            if c:
                r['eliminador'] = {
                    'nombre': c['nombre'],
                    'apellido': c['apellido'],
                    'dni': c['dni'],
                    'oficinas': _obtener_oficinas(c['id'],token)
                }
            justificaciones.append(r)

        try:
            off = [j['usuario']['oficinas'] for j in justificaciones if 'usuario' in j]
            logging.info(off)
        except:
            pass
        return justificaciones
        
        


    @classmethod
    def _procesar_justificacion_reporte(cls, j):
        r = j.__json__()
        if j.creador_id:
            r['creador'] = cls.cache_usuarios.obtener_usuario_por_uid(j.creador_id)
        if j.actualizador_id:
            r['actualizador'] = cls.cache_usuarios.obtener_usuario_por_uid(j.actualizador_id)
        if j.eliminador_id:
            r['eliminador'] = cls.cache_usuarios.obtener_usuario_por_uid(j.eliminador_id)
        return r

    """
        ////////////////////////////////////
    """

    @classmethod
    def justificacion(cls, session, jid):
        return session.query(Justificacion).filter(Justificacion.id == jid).one_or_none()

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
    def eliminarFechaJustificadaJefe(cls, session, jid, autorizador_id=None, uid=None):
        justificacion = session.query(FechaJustificada).filter(FechaJustificada.id == jid).one()
        if justificacion.usuario_id != uid:
            raise Exception('usuario erróneo')
        return cls.eliminarFechaJustificada(session, jid, autorizador_id)

    @classmethod
    def eliminarFechaJustificada(cls, session, jid, autorizador_id=None):

        justificacion = session.query(FechaJustificada).filter(FechaJustificada.id == jid).one()
        justificacion.eliminado = datetime.datetime.now()
        if not autorizador_id:
            autorizador_id = justificacion.usuario_id
        justificacion.eliminador_id = autorizador_id

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

        #Consulta justificacion existente
        just = fj["justificacion"]
        q = session.query(FechaJustificada).filter(and_(FechaJustificada.usuario_id == fj['usuario_id'], FechaJustificada.justificacion_id == just['id']))
        q = q.filter(and_(FechaJustificada.eliminado == None, FechaJustificada.fecha_inicio == fj['fecha_inicio'],FechaJustificada.fecha_fin == fj['fecha_fin']))
        if q.count() > 0:
            raise Exception('Fecha justificada existente para ese usuario')
                
        j = FechaJustificada()
        j.id = str(uuid.uuid4())
        j.fecha_inicio = fj["fecha_inicio"]
        j.fecha_fin = fj["fecha_fin"]
        j.usuario_id = fj["usuario_id"] if 'usuario_id' in fj else None
        j.notas = fj['notas'] if 'notas' in fj else ''
        j.justificacion_id = just["id"]
        j.creador_id = autorizador_id
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
    def crear_log_por_usuario(cls, session, uid, tz='America/Argentina/Buenos_Aires'):
        logger = logging.getLogger('assistance.model.zkSoftware')

        token = cls.api._get_token()
        usuario = cls.cache_usuarios.obtener_usuario_por_uid(uid, token=token)
        dni = usuario['dni']

        log = Marcacion()
        log.id = str(uuid.uuid4())
        log.usuario_id = uid
        #esta como reloj remoto en la base - TODO: analizar cual es la mejor opción.
        log.dispositivo_id = '95d40ffa-1e13-4f6f-905a-b3a2140bd57d'
        # 3 => remoto
        log.tipo = 3
        log.marcacion = datetime.datetime.now().astimezone(pytz.timezone(tz))
        session.add(log)

        r = {'estado':'agregada', 'marcacion':log, 'dni':dni, 'nombre':usuario['nombre'], 'apellido':usuario['apellido']}
        logger.info(r)
        return r

    @classmethod
    def sincronizar_reloj(cls, session, rid):
        token = cls.api._get_token()
        borrar = cls.eliminar_logs_relojes
        """
            TODO: analizar para despues eliminar esto. por ahora se borran los logs solo en determinados horarios.
        """
        ahora = datetime.datetime.now().time()
        if not datetime.time(3,13) < ahora < datetime.time(3,37):
           borrar = False 
        """
            --------------
        """


        estados = RelojesModel.sincronizar(session, 
                                rid=rid, 
                                zona_horaria='America/Argentina/Buenos_Aires', 
                                borrar=borrar, 
                                cache_usuarios=cls.cache_usuarios, 
                                token=token)
        for e in estados:
            yield e
    