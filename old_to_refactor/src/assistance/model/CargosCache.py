import pymongo
from pymongo.operations import IndexModel

import datetime

class CargosAPI:

    def __init__(self, api_url, api):
        self.url = api_url
        self.api = api

    def _get_cargos_por_uid(self, uid, token=None):
        query = f"{self.url}/usuarios/{uid}/designaciones"
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        lid = r.json()
        if lid:
            return lid
        return None


class CargosGetters:

    def __init__(self, cargos_api):
        self.api = cargos_api

    def obtener_cargos_por_uid(self, uid, token=None):
        return self.api._get_cargos_por_uid(uid, token)


class CargosCache:

    def __init__(self, mongo_url, getters, prefijo='_assistance_', timeout=60 * 15):
        db = '{}_{}'.format(prefijo, self.__class__.__name__)
        self.mongo = pymongo.MongoClient(mongo_url)[db]
        self.prefijo = prefijo
        self.timeout = timeout
        self.getters = getters

        # indices para la expiración
        for c in ['cargos_por_usuario']:
            self.mongo.drop_collection(c)
            self.mongo[c].create_index('insertadoEn',expireAfterSeconds=self.timeout)

    def setear_cargos_por_usuario_id(self, uid, cargos):
        fecha = datetime.datetime.utcnow()
        for c in cargos:
            c['usuario_id'] = uid
            c['insertadoEn'] = fecha        
        self.mongo.cargos_por_usuario.insert_many(cargos)

    def obtener_cargos_por_usuario_id(self, uid, token=None):
        ccargos = self.mongo.cargos_por_usuario.find({'usuario_id':uid})
        cargos = [c for c in ccargos]
        if len(cargos) > 0:
            for c in cargos:
                if '_id' in c:
                    del c['_id']
            return cargos
        cargos = self.getters.obtener_cargos_por_uid(uid, token)
        if not cargos or len(cargos) <= 0:
            return []
        self.setear_cargos_por_usuario_id(uid, cargos)
        return cargos
