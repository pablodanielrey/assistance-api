import pymongo
from pymongo.operations import IndexModel
import datetime
import pytz
from datetime import timedelta
from assistance.model import obtener_session
from assistance.model.entities import Marcacion
import json

class MarcacionesGetter:

    def obtener_marcaciones_por_uid_por_tiempo(self, uid, dias=2):
        """
        Obtiene de la DB las marcaciones hasta 2 dias atras (por defecto) para el usuario_id pasado como parametro
        """
        fecha = datetime.datetime.now() - timedelta(days=dias)
        marcaciones = []
        with obtener_session() as session:
            mmarcaciones = session.query(Marcacion).filter(Marcacion.usuario_id == uid, Marcacion.marcacion > fecha).order_by(Marcacion.marcacion).all()
            for m in mmarcaciones:
                marcaciones.append(m)
            return marcaciones

    def existe_marcacion_de_usuario(self, uid, marcacion, token=None,tz='America/Argentina/Buenos_Aires'):
        pass


class MarcacionesCache:

    def __init__(self, mongo_url, marcaciones_getter, prefijo='_assistance_', timeout=60 * 15):
        db = '{}_{}'.format(prefijo, self.__class__.__name__)
        self.mongo = pymongo.MongoClient(mongo_url)[db]
        self.prefijo = prefijo
        self.timeout = timeout
        self.getter = marcaciones_getter

        # indices para la expiración
        for c in ['marcaciones_por_usuario']:
            self.mongo.drop_collection(c)
            self.mongo[c].create_index('insertadoEn',expireAfterSeconds=self.timeout)

    def setear_marcacion_por_usuario_id(self, uid, marc):
        """
        Inserta en la cache los objetos marcacion enviados, si existe uid los actualiza. Sino lo inserta nuevos
        """
        fecha = datetime.datetime.utcnow()
        marcaciones = {}
        marcaciones['marcaciones']= [m.__json__() for m in marc]
        marcaciones['usuario_id'] = uid
        marcaciones['insertadoEn'] = fecha
        if self.mongo.marcaciones_por_usuario.update_one({'usuario_id':uid}, { "$set":marcaciones }).modified_count <= 0:
            self.mongo.marcaciones_por_usuario.insert_one(marcaciones)

    def obtener_marcaciones_por_usuario(self, uid):
        """
        Obtiene de la cache las marcaciones para el usuario_id pasado como parametro
        """
        resultado = self.mongo.marcaciones_por_usuario.find({'usuario_id':uid})
        ret = []
        for m in resultado:
            ret.extend(m['marcaciones'])
        return ret

    def existe_marcacion_de_usuario(self, uid, marcacion, tz='America/Argentina/Buenos_Aires'):
        """
        Comprueba si existe en la cache la marcacion pasada como parametro para el usuario_id pasado como parametro,
        Si no existe la obtiene desde el getter y la inserta en la cache
        """
        timezone = pytz.timezone(tz)
        marcaciones = self.obtener_marcaciones_por_usuario(uid)

        fechas = []
        for m in marcaciones:
            corregida = m['marcacion'].replace(tzinfo=pytz.UTC)
            fechas.append(corregida.astimezone(timezone))
        if marcacion in fechas:
            return True
        else:
            marcaciones = self.getter.obtener_marcaciones_por_uid_por_tiempo(uid)
            fechas = [m.marcacion.astimezone(timezone) for m in marcaciones]
            if marcacion in fechas:
                self.setear_marcacion_por_usuario_id(uid, marcaciones)
                return True
            else:
                return False
            
