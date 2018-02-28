from sqlalchemy import or_
from sqlalchemy.orm import joinedload, with_polymorphic
from datetime import datetime, date, timedelta
import requests
import os
import logging
import uuid

import oidc
from oidc.oidc import ClientCredentialsGrant

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
    def reporte(cls, uid, inicio, fin):
        assert uid is not None
        fin = fin if fin else date.today()
        inicio = inicio if inicio else fin - timedelta(days=7)

        session = Session()

        try:
            u = session.query(Usuario).filter(Usuario.id == uid).one_or_one()
            Reporte.generarReporte(session, u, inicio, fin)

        finally:
            session.close()

    @classmethod
    def usuario(cls, uid, retornarClave=False):
        query = cls.usuarios_url + '/usuarios/' + uid
        query = query + '?c=True' if retornarClave else query
        r = cls.api(query)
        if not r.ok:
            return []

        usr = r.json()
        session = Session()
        try:
            # ausr = session.query(Usuario).filter(Usuario.id == uid).one_or_none()
            ausr = None
            if ausr:
                return {
                    'usuario': usr,
                    'asistencia': ausr
                }
            else:
                return {
                    'usuario': usr
                }

        finally:
            session.close()

    @classmethod
    def relojes(cls, session):
        return session.query(Reloj).all()

    @classmethod
    def sincronizar(cls, session):
        logger = logging.getLogger('sincronizar')
        q = session.query(Reloj).filter(Reloj.activo).all()
        zks = [ZkSoftware(r.ip, r.puerto) for r in q]

        all_logs = []
        for zk in zks:
            logs = zk.getAttLog()
            if len(logs) <= 0:
                logger.info(logs)
                continue

            aSincronizar = []
            for l in logs:
                dni = l['PIN']

                ''' localizo la fecha '''
                """
                m = l['DateTime']
                tz = pytz.timezone(zk.zona_horaria)


                log = Marcacion()
                log.id = str(uuid.uuid4())
                log.usuario_id = None
                log.deviceId = zk.id
                log.verifyMode = l['Verified']
                log.log = utcaware
                """
            all_logs.extend(logs)

        return all_logs

    @classmethod
    def reporte(cls, uid, inicio, fin):
        return None
