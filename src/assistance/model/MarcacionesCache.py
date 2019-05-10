import pymongo
from pymongo.operations import IndexModel
import datetime
import pytz
from datetime import timedelta
from assistance.model import obtener_session
from assistance.model.entities import Marcacion

class MarcacionesCache:

    def __init__(self, mongo_url, prefijo='_assistance_', timeout=60 * 15):
        db = '{}_{}'.format(prefijo, self.__class__.__name__)
        self.mongo = pymongo.MongoClient(mongo_url)[db]
        self.prefijo = prefijo
        self.timeout = timeout

        # indices para la expiración
        #for c in ['marcaciones_por_usuario']:
        #    self.mongo.drop_collection(c)
        #    self.mongo[c].create_index('insertadoEn',expireAfterSeconds=self.timeout)

    def obtener_marcaciones_por_uid(self, uid, token=None):
        import json
        fecha = datetime.datetime.now() - timedelta(days=2)
        marcaciones = []
        with obtener_session() as session:
            mmarcaciones = session.query(Marcacion).filter(Marcacion.usuario_id == uid, Marcacion.marcacion > fecha).order_by(Marcacion.marcacion).all()
            for m in mmarcaciones:
                marcaciones.append(m.__json__())
            return marcaciones

    def setear_marcacion_por_usuario_id(self, uid, marc):
        fecha = datetime.datetime.utcnow()
        marcaciones = {}
        marcaciones['marcaciones']= marc
        marcaciones['usuario_id'] = uid
        marcaciones['insertadoEn'] = fecha        
        self.mongo.marcaciones_por_usuario.insert_one(marcaciones)

    def existe_marcacion_de_usuario(self, uid, marcacion, token=None,tz='America/Argentina/Buenos_Aires'):
        timezone =pytz.timezone(tz)
        resultado = self.mongo.marcaciones_por_usuario.find({'usuario_id':uid})
        marcaciones = []
        for r in resultado:
            for m in r['marcaciones']:
                marcaciones.append((m.astimezone(timezone) - timedelta(hours=3)))
        if marcacion in marcaciones:
            return True
        else:
            marcaciones = [m['marcacion'].astimezone(timezone) for m in self.obtener_marcaciones_por_uid(uid, token)]
            if marcacion in marcaciones:
                self.setear_marcacion_por_usuario_id(uid, marcaciones)
                return True
            else:
                return False
            
