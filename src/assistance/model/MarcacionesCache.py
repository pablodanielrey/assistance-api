import pymongo
from pymongo.operations import IndexModel
import datetime
from assistance.model.entities import Marcacion

class MarcacionesGetters:
    """Ver si es necesario"""
    def __init__(self, marcaciones_api):
        self.api = marcaciones_api

    def obtener_marcaciones_por_uid(self, uid, marcaciones=[],token=None):
        fecha = datetime.datetime.now() - timedelta(days=2)
        with obtener_session() as session:
            marcaciones = session.query(Marcacion).filter(and_(Marcacion.usuario_id == uid, Marcacion.marcacion > fecha)).all()
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
            
