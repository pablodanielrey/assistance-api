import pytz
import logging
import uuid
import json

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, with_polymorphic
from datetime import datetime, date, timedelta

from assistance.firmware.ZKSoftware import ZKSoftware
from assistance.model.entities import Reloj, Marcacion

class RelojesModel:


    MARCACION_INTERNA = {
        'CLAVE':0,
        'HUELLA':1,
        'TARJETA':2,
        'REMOTO':100
    }

    MAPEOS_TIPO_MARCACION = {
        'U560-C/ID': {
            0: MARCACION_INTERNA['CLAVE'],
            1: MARCACION_INTERNA['HUELLA'],
            2: MARCACION_INTERNA['TARJETA']
        },
        'UA760': {
            1: MARCACION_INTERNA['HUELLA'],
            3: MARCACION_INTERNA['CLAVE'],
            4: MARCACION_INTERNA['TARJETA']
        }
    }

    @classmethod
    def _insertar_marcaciones(cls, session, rid, mapeo_marcacion, cache_usuarios, token, marcaciones):
        logger_marcacion = logging.getLogger('assistance.model.zkSoftware.marcacion')
        logger_duplicada = logging.getLogger('assistance.model.zkSoftware.duplicada')
        estados = []
        for l in marcaciones:
            dni = l.user_id
            usuario = cache_usuarios.obtener_usuario_por_dni(dni, token=token)
            marcacion = l.att_time

            ms = session.query(Marcacion).filter(and_(Marcacion.usuario_id == usuario['id'], Marcacion.marcacion == marcacion)).all()
            if len(ms) <= 0:
                log = Marcacion()
                log.id = str(uuid.uuid4())
                log.usuario_id = usuario['id']
                log.dispositivo_id = rid
                log.tipo = mapeo_marcacion[l.ver_type] if l.ver_type in mapeo_marcacion else l.ver_type
                log.marcacion = marcacion
                session.add(log)
                session.commit()
                r = {'estado':'nueva', 'marcacion':log, 'dni':dni, 'nombre':usuario['nombre'], 'apellido':usuario['apellido']}
                logger_marcacion.info(r)
                estados.append(r)
            else:
                for m in ms:
                    r = {'estado':'duplicada', 'marcacion':m, 'dni':dni, 'nombre':usuario['nombre'], 'apellido':usuario['apellido']}
                    logger_duplicada.info(r)
                    estados.append(r)
        return estados

    @classmethod
    def _localizar_fechas(cls, marcaciones, zona_horaria='America/Argentina/Buenos_Aires'):
        timezone = pytz.timezone(zona_horaria)
        for l in marcaciones:
            pDate = l.att_time.replace(microsecond=0,tzinfo=None)
            zpDate = timezone.localize(pDate)
            l.att_time = zpDate

    @classmethod
    def sincronizar(cls, session, rid, zona_horaria='America/Argentina/Buenos_Aires', borrar=False, cache_usuarios=None, token=None):
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zona_horaria = reloj.zona_horaria
        if not zona_horaria:
            zona_horaria = 'America/Argentina/Buenos_Aires'

        estados = []
        z = ZKSoftware(reloj.ip,reloj.puerto)
        mapeo_marcaciones = cls.MAPEOS_TIPO_MARCACION[reloj.modelo]
        z.connect()
        try:
            if borrar:
                z.disable_device()
                try:
                    marcaciones = z.obtener_marcaciones()
                    cls._localizar_fechas(marcaciones, zona_horaria)
                    estados = cls._insertar_marcaciones(
                                            session=session,
                                            rid=reloj.id, 
                                            mapeo_marcacion=mapeo_marcaciones, 
                                            cache_usuarios=cache_usuarios, 
                                            token=token, 
                                            marcaciones=marcaciones)
                    z.borrar_marcaciones()
                finally:
                    z.enable_device()
            else:
                marcaciones = z.obtener_marcaciones()
                cls._localizar_fechas(marcaciones, zona_horaria)
                estados = cls._insertar_marcaciones(
                                        session=session,
                                        rid=reloj.id, 
                                        mapeo_marcacion=mapeo_marcaciones, 
                                        cache_usuarios=cache_usuarios, 
                                        token=token, 
                                        marcaciones=marcaciones)

        finally:
            z.disconnect()

        return estados
    