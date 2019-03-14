import pymongo
from pymongo.operations import IndexModel

import datetime

class LugaresAPI:

    def __init__(self, api_url, api):
        self.url = api_url
        self.api = api

    def _get_lugar_lid(self, lid, token=None):
        query = '{}/lugares/{}'.format(self.url, lid)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        lid = r.json()
        if lid:
            return lid
        return None

    def _get_arbol_por_lid(self, lid, token=None):
        query = '{}/lugares/{}/arbol'.format(self.url, lid)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        arbol = r.json()
        return arbol

    def _get_sublugares_lid(self, lid, token=None):
        query = '{}/lugares/{}/sublugares'.format(self.url, lid)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        lids = r.json()
        if lids and len(lids) > 0:
            return lids
        return None

    def _get_lugares_por_uid(self, uid, token=None):
        query = '{}/usuarios/{}/lugares'.format(self.url, uid)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        lids = r.json()
        if lids and len(lids) > 0:
            return lids
        return None

    def _get_subusuarios_por_lugar(self, lid, token=None):
        query = '{}/lugares/{}/subusuarios'.format(self.url, lid)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        uids = r.json()
        if uids and len(uids) > 0:
            return uids
        return None


class LugaresGetters:
    def __init__(self, lugares_api):
        self.api = lugares_api

    def obtener_lugar_por_id(self, lid, token=None):
        return self.api._get_lugar_lid(lid, token)

    def obtener_sublugares_por_lugar(self, lid, token=None):
        return self.api._get_sublugares_lid(lid, token)

    def obtener_subusuarios_por_lugar(self, lid, token=None):
        return self.api._get_subusuarios_por_lugar(lid, token)

    def obtener_lugares_por_usuario(self, uid, token=None):
        return self.api._get_lugares_por_uid(uid, token)

    def obtener_arbol_por_lugar(self, lid, token=None):
        return self.api._get_arbol_por_lid(lid, token)


class LugaresCache:

    def __init__(self, mongo_url, getters, prefijo='_assistance_', timeout=60 * 15):
        db = '{}_{}'.format(prefijo, self.__class__.__name__)
        self.mongo = pymongo.MongoClient(mongo_url)[db]
        self.prefijo = prefijo
        self.timeout = timeout
        self.getters = getters

        # indices para la expiración
        for c in ['lugares','arboles','sublugares_lugar','sublugares_usuario','subusuarios']:
            self.mongo.drop_collection(c)
            self.mongo[c].create_index('insertadoEn',expireAfterSeconds=self.timeout)

    def setear_lugar(self, lugar):
        lugar['insertadoEn'] = datetime.datetime.utcnow()
        self.mongo.lugares.insert_one(lugar)

    def obtener_lugar_por_id(self, lid, token=None):
        lugar = self.mongo.lugares.find_one({'id':lid})
        if not lugar:
            lugar = self.getters.obtener_lugar_por_id(lid, token)
            if not lugar:
                return None
            self.setear_lugar(lugar)
        if '_id' in lugar:
            del lugar['_id']
        return lugar

    def setear_arbol_por_lugar_id(self, lid, arbol):
        arbol['id'] = lid
        arbol['insertadoEn'] = datetime.datetime.utcnow()
        self.mongo.arboles.insert_one(arbol)

    def obtener_arbol_por_lugar_id(self, lid, token=None):
        arbol = self.mongo.arboles.find_one({'id':lid})
        if not arbol:
            arbol = self.getters.obtener_arbol_por_lugar(lid, token)
            if not arbol:
                return None
            self.setear_arbol_por_lugar_id(lid, arbol)
        if '_id' in arbol:
            del arbol['_id']
        return arbol

    def setear_sublugares_por_lugar_id(self, lid, lids=[]):
        fecha = datetime.datetime.utcnow()
        lugares = [
            {
                'id':l,
                'padre_id': lid,
                'insertadoEn':fecha
            }
            for l in lids
        ]
        self.mongo.sublugares_lugar.insert_many(lugares)

    def obtener_sublugares_por_lugar_id(self, lid, token=None):
        parametros = {
            'padre_id': lid
        }
        lugares = self.mongo.sublugares_lugar.find(parametros)
        lids = [l['id'] for l in lugares]
        if len(lids) > 0:
            return lids
        lids = self.getters.obtener_sublugares_por_lugar(lid, token)
        if not lids or len(lids) <= 0:
            return []
        self.setear_sublugares_por_lugar_id(lid, lids)
        return lids

    def setear_subusuarios_por_lugar_id(self, lid, usuarios):
        fecha = datetime.datetime.utcnow()
        for l in usuarios:
            l['lugar_id'] = lid
            l['insertadoEn'] = fecha        
        self.mongo.subusuarios.insert_many(usuarios)

    def obtener_subusuarios_por_lugar_id(self, lid, token=None):
        cusuarios = self.mongo.subusuarios.find({'lugar_id':lid})
        usuarios = [u for u in cusuarios]
        if len(usuarios) > 0:
            for u in usuarios:
                if '_id' in u:
                    del u['_id']
            return usuarios
        usuarios = self.getters.obtener_subusuarios_por_lugar(lid, token)
        if not usuarios or len(usuarios) <= 0:
            return []
        self.setear_subusuarios_por_lugar_id(lid, usuarios)
        return usuarios

    def setear_lugares_por_usuario_id(self, uid, lids):
        fecha = datetime.datetime.utcnow()
        lugares = [
            {
                'id':l,
                'usuario_id': uid,
                'insertadoEn':fecha
            }
            for l in lids
        ]
        self.mongo.sublugares_usuario.insert_many(lugares)

    def obtener_lugares_por_usuario_id(self, uid, token=None):
        lugares = self.mongo.sublugares_usuario.find({'usuario_id':uid})
        lids = [l['id'] for l in lugares]
        if len(lids) > 0:
            return lids
        lids = self.getters.obtener_lugares_por_usuario(uid, token)
        if not lids:
            return []
        self.setear_lugares_por_usuario_id(uid, lids)
        return lids