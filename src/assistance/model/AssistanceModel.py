from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, with_polymorphic
from datetime import datetime, date, timedelta
import requests
import os
import logging
import uuid
from dateutil import parser
import oidc
from oidc.oidc import ClientCredentialsGrant

from assistance.model.zkSoftware import ZkSoftware
from .entities import *
from . import Session

class AssistanceModel:

    verify = True
    usuarios_url = os.environ['USERS_API_URL']
    client_id = os.environ['OIDC_CLIENT_ID']
    client_secret = os.environ['OIDC_CLIENT_SECRET']


    @classmethod
    def _get_token(cls):
        ''' obtengo un token mediante el flujo client_credentials para poder llamar a la api de usuarios '''
        grant = ClientCredentialsGrant(cls.client_id, cls.client_secret)
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
    def reporte(cls, session, uid, inicio, fin):
        assert uid is not None
        fin = fin if fin else date.today()
        inicio = inicio if inicio else fin - timedelta(days=7)

        u = session.query(Usuario).filter(Usuario.id == uid).one_or_none()
        if u is None:
            return []
        query = cls.usuarios_url + '/usuarios/' + uid
        r = cls.api(query)
        if not r.ok:
            return []

        usr = r.json()
        return Reporte.generarReporte(session, usr, inicio, fin)


    @classmethod
    def horario(cls, session, uid, fecha):
        assert uid is not None
        fecha = fecha if fecha else date.today()

        u = session.query(Usuario).filter(Usuario.id == uid).one_or_none()
        if u is None:
            return {}


        query = cls.usuarios_url + '/usuarios/' + u.id
        r = cls.api(query)
        if not r.ok:
            return []

        usr = r.json()

        horarios = []
        hsSemanales = 0

        for i in range(0, 7):
            actual = fecha + timedelta(days=i)

            q = session.query(Horario)
            q = q.filter(Horario.usuario_id == u.id, Horario.dia_semanal == actual.weekday(), Horario.fecha_valido <= actual)
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
        return {
                'horarios': horarios,
                'horasSemanales': {'horas': hsSem, 'minSem': minSem},
                'usuario':usr
                }

    @classmethod
    def crearHorario(cls, session, horarios):
        for h in horarios:
            horario = Horario()

            horario.fecha_valido = parser.parse(h['fecha_valido']).date() if h['fecha_valido'] else None
            horario.dia_semanal = h['dia_semanal']
            horario.hora_entrada = h['hora_entrada']
            horario.hora_salida = h['hora_salida']
            horario.usuario_id = h['usuario_id']
            horario.id = str(uuid.uuid4())
            session.add(horario)


    @classmethod
    def usuario(cls, session, uid, retornarClave=False):
        query = cls.usuarios_url + '/usuarios/' + uid
        query = query + '?c=True' if retornarClave else query
        r = cls.api(query)
        if not r.ok:
            return []

        usr = r.json()
        ausr = session.query(Usuario).filter(Usuario.id == uid).one_or_none()
        if ausr:
            return {
                'usuario': usr,
                'asistencia': ausr
            }
        else:
            return {
                'usuario': usr
            }

    @classmethod
    def usuarios(cls, session, search, retornarClave, offset, limit, fecha):
        logging.debug(fecha)
        query = cls.usuarios_url + '/usuarios/'
        params = {}
        if search:
            params['q'] = search
        if offset:
            params['offset'] = offset
        if limit:
            params['limit'] = limit
        if fecha:
            params['f'] = fecha
        if retornarClave:
            params['c'] = True

        logging.debug(query)
        r = cls.api(query, params)
        if not r.ok:
            return []

        usrs = r.json()
        idsProcesados = {}

        rusers = []
        for u in usrs:
            uid = u['id']
            idsProcesados[uid] = u
            susrs = session.query(Usuario).filter(Usuario.id == uid).one_or_none()
            rusers.append({
                'usuario': u,
                'asistencia': susrs
            })

        if not fecha:
            return rusers


        """ tengo en cuenta los que se pudieron haber agregado a asistencia despues """
        token = cls._get_token()
        q = None
        q = session.query(Usuario).filter(or_(Usuario.creado >= fecha, Usuario.actualizado >= fecha)).all()
        for u in q:
            if u.id not in idsProcesados.keys():
                query = '{}/{}/{}'.format(cls.usuarios_url, 'usuarios', u.id)
                r = cls.api(query, params={'c':True}, token=token)
                if not r.ok:
                    continue
                usr = r.json()
                if usr:
                    rusers.append({
                        'agregado': True,
                        'usuario': usr,
                        'asistencia': u
                    })
        return rusers

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
    def _sinc_usuario_por_dni(cls, session, dni, retornarClave=False, token=None):
        '''
            Usado internamente para obtener un usuario por dni
            NOTA: AGREGA AL USUARIO A LAS TABLAS DE ASISTENCIA SI ES QUE NO EXISTE!!!!
        '''
        ausr = session.query(Usuario).filter(Usuario.dni == dni).one_or_none()
        if ausr:
            return ausr

        query = cls.usuarios_url + '/usuarios/'
        params = {}
        if retornarClave:
            params['c'] = True
        params = {'q':dni}
        r = cls.api(query,params=params,token=token)
        if not r.ok:
            raise Exception(r.text)
        import json
        logging.debug(r.json())
        for usuario in r.json():
            if usuario['dni'] == dni:
                u = session.query(Usuario).filter(Usuario.dni == dni).one_or_none()
                if not u:
                    u = Usuario()
                    u.id = usuario['id']
                    u.dni = usuario['dni']
                    session.add(u)
                return u
        raise Exception('No se encuentra usuario con ese dni')

    @classmethod
    def sincronizar(cls, session):
        q = session.query(Reloj.id).filter(Reloj.activo).all()
        sincronizados = []
        for rid in q:
            sincronizados.extend(cls.sincronizar_reloj(session, rid))
        return sincronizados

    @classmethod
    def sincronizar_reloj(cls, session, rid):
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zona_horaria = reloj.zona_horaria
        if not zona_horaria:
            zona_horaria = 'America/Argentina/Buenos_Aires'
        zk = {'reloj':reloj, 'api':ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=zona_horaria)}
        logs = zk['api'].getAttLog()
        if len(logs) <= 0:
            logging.info(logs)
            return []

        token = cls._get_token()
        sincronizados = []
        for l in logs:
            dni = l['PIN'].strip().lower()
            usuario = cls._sinc_usuario_por_dni(session, dni, token=token)
            marcacion = l['DateTime']

            if session.query(Marcacion).filter(and_(Marcacion.usuario_id == usuario.id, Marcacion.marcacion == marcacion)).count() <= 0:
                log = Marcacion()
                log.id = str(uuid.uuid4())
                log.usuario_id = usuario.id
                log.dispositivo_id = zk['reloj'].id
                log.tipo = l['Verified']
                log.marcacion = marcacion
                session.add(log)

                ''' para que no tire error el serializador de json le hago un expunge '''
                r = session.query(Marcacion).filter(Marcacion.id == log.id).options(joinedload('usuario')).one()
                session.expunge(r.usuario)
                session.expunge(r)
                sincronizados.append(r)
            else:
                logging.warn('Marcación duplicada {} {} {}'.format(usuario.id, dni, marcacion))

        return sincronizados
