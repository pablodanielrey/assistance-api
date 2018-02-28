from sqlalchemy import or_
from sqlalchemy.orm import joinedload, with_polymorphic
from datetime import datetime, date, timedelta
import requests
import os
import logging
import uuid

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
    def _usuario_por_dni(cls, session, dni, retornarClave=False, token=None):
        ''' usado internamente para obtener un usuario por dni '''
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
                u = Usuario()
                u.id = usuario['id']
                u.dni = usuario['dni']
                session.add(u)
                return u
        raise Exception('No se encuentra usuario con ese dni')

    @classmethod
    def relojes(cls, session):
        return session.query(Reloj).all()

    @classmethod
    def sincronizar(cls, session):
        q = session.query(Reloj).filter(Reloj.activo).all()
        zks = [{'reloj':r, 'api':ZkSoftware(host=r.ip, port=r.puerto, timezone=r.zona_horaria)} for r in q]

        token = cls._get_token()

        aSincronizar = []
        for zk in zks:
            logs = zk['api'].getAttLog()
            if len(logs) <= 0:
                logging.info(logs)
                continue

            for l in logs:
                dni = l['PIN'].strip().lower()
                usuario = cls._usuario_por_dni(session, dni, token=token)

                log = Marcacion()
                log.id = str(uuid.uuid4())
                log.usuario_id = usuario.id
                log.dispositivo_id = zk['reloj'].id
                log.tipo = l['Verified']
                log.marcacion = l['DateTime']
                aSincronizar.append(log)

        return aSincronizar

    @classmethod
    def reporte(cls, uid, inicio, fin):
        return None
