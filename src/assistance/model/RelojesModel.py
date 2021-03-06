import pytz
import logging
import uuid
import json


"""
    //////////////////////////////////////////////////////
    ESQUEMA DE IMPORTACION DINAMICA DEL RELOJ SELECCIONADO
    //////////////////////////////////////////////////////
"""

import os
zkmodule = os.environ['ZKSOFTWARE_DEVICE_MODULE']
zkdevice = os.environ['ZKSOFTWARE_DEVICE_CLASS']

import importlib
module = importlib.import_module(zkmodule)
ZKSOFTWAREDEVICE_ = getattr(module, zkdevice)

"""
    /////////////////////////////////////////
"""


from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, with_polymorphic
from datetime import datetime, date, timedelta

from assistance.firmware.ZKSoftware import ZkSoftwareDevice
from assistance.firmware.PyZKDevice import PyZKDevice
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
    def _insertar_marcaciones(cls, session, rid, mapeo_marcacion, cache_usuarios, cache_marcaciones, token, marcaciones):
        logger_marcacion = logging.getLogger('assistance.model.zkSoftware.marcacion')
        logger_persona_inexistente = logging.getLogger('assistance.model.zkSoftware.persona_inexistente')
        excepciones = []
        estados = []
        for l in marcaciones:
            try:
                dni = l.user_id
                try:
                    usuario = cache_usuarios.obtener_usuario_por_dni(dni, token=token)
                except Exception as ex:
                    usuario = None
                    
                marcacion = l.att_time
                #Si no existe usuario logueo el DNI y la Marcacion
                if not usuario:
                    r = {'error':'No existe usuario para ese dni', 'dni':dni, 'marcacion': marcacion}
                    logger_persona_inexistente.info(r)
                    estados.append(r)
                    continue
                
                uid = usuario['id']
                if cache_marcaciones.existe_marcacion_de_usuario(uid, marcacion):
                    continue
                
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
                    r = {'estado':'nueva', 'marcacion':log.__json__(), 'dni':dni, 'nombre':usuario['nombre'], 'apellido':usuario['apellido']}
                    logger_marcacion.info(r)
                    estados.append(r)

                else:
                    for m in ms:
                        r = {'estado':'duplicada', 'marcacion':m.__json__(), 'dni':dni, 'nombre':usuario['nombre'], 'apellido':usuario['apellido']}
                        estados.append(r)
            except Exception as e:
                excepciones.append(e)
        if len(excepciones) > 0:
            for e in excepciones:
                raise e
        return estados

    @classmethod
    def _localizar_fechas(cls, marcaciones, zona_horaria='America/Argentina/Buenos_Aires'):
        timezone = pytz.timezone(zona_horaria)
        for l in marcaciones:
            pDate = l.att_time.replace(microsecond=0,tzinfo=None)
            zpDate = timezone.localize(pDate)
            l.att_time = zpDate

    @classmethod
    def sincronizar(cls, session, rid, zona_horaria='America/Argentina/Buenos_Aires', borrar=False, cache_usuarios=None, cache_marcaciones=None, token=None):
        reloj = session.query(Reloj).filter(Reloj.id == rid).one()
        zona_horaria = reloj.zona_horaria
        if not zona_horaria:
            zona_horaria = 'America/Argentina/Buenos_Aires'

        estados = []
        #z = ZKSoftware(reloj.ip,reloj.puerto)
        #z = PyZKDevice(reloj.ip, reloj.puerto)
        z = ZKSOFTWAREDEVICE_(reloj.ip, reloj.puerto)
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
                                            cache_marcaciones=cache_marcaciones, 
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
                                        cache_marcaciones=cache_marcaciones, 
                                        token=token, 
                                        marcaciones=marcaciones)

        finally:
            z.disconnect()

        return estados
    