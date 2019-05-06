import pymongo
from pymongo.operations import IndexModel

import datetime

class MarcacionesAPI:
    """Ver como acceder a la api directamente"""
    def __init__(self, api_url, api):
        self.url = api_url
        self.api = api

    def _get_marcaciones_por_uid(self, uid, token=None):
        query = f"{self.url}/usuarios/{uid}/logs"
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        lid = r.json()
        if lid:
            return lid
        return None


class MarcacionesGetters:
    """Ver si es necesario"""
    def __init__(self, marcaciones_api):
        self.api = marcaciones_api

    def obtener_marcaciones_por_uid(self, uid, marcaciones=[],token=None):
        with obtener_session() as session:
            marcaciones = session.selecc...
            return marcaciones


class MarcacionesCache:

    def __init__(self, mongo_url, getters, prefijo='_assistance_', timeout=60 * 15):
        db = '{}_{}'.format(prefijo, self.__class__.__name__)
        self.mongo = pymongo.MongoClient(mongo_url)[db]
        self.prefijo = prefijo
        self.timeout = timeout
        self.getters = getters

        # indices para la expiración
        for c in ['marcaciones_por_usuario']:
            self.mongo.drop_collection(c)
            self.mongo[c].create_index('insertadoEn',expireAfterSeconds=self.timeout)

    def setear_marcacion_por_usuario_id(self, uid, marcaciones):
        ###TODO: Hacer drop de la coleccion de datos para al UID e insertar las nuevas marcaciones
        
        fecha = datetime.datetime.utcnow()
        for m in marcaciones:
            m['usuario_id'] = uid
            m['insertadoEn'] = fecha        
        self.mongo.marcaciones_por_usuario.insert_many(marcaciones)

    def existe_marcacion_de_usuario(self, uid, marcacion, token=None):
        mmarcaciones = self.mongo.marcaciones_por_usuario.find({'usuario_id':uid})
        marcaciones = [m for m in mmarcaciones]
        if (len(marcaciones) > 0) and (marcacion in marcaciones):
            return True
        else:
            marcaciones = self.getters.obtener_marcaciones_por_uid(uid, marcaciones, token)
            if marcaccion in marcaciones:
                self.setear_marcacion_por_usuario_id(uid, marcaciones)
                return True
            else:
                return False
            
