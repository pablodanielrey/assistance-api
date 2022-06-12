import socket
import struct
import datetime
import pytz
from .defs import *

class AttLog:
    def __init__(self,user_id,att_time,ver_type,ver_state):
        self.user_id = user_id
        self.att_time = att_time
        self.ver_type = ver_type
        self.ver_state = ver_state

    def __json__(self):
        d = self.__dict__
        return json.dumps(d)

class ZkSoftwareDevice:
    """
        Interface de los relojes de asistencia
    """

    def disconnect(self):
        pass

    def connect(self):
        pass

    def enable_device(self):
        pass

    def disable_device(self, timer=None):
        pass

    def obtener_marcaciones(self):
        pass


    def borrar_marcaciones(self):
        pass