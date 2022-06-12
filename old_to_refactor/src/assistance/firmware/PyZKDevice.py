import pytz
from zk import ZK, const

from .ZKSoftware import ZkSoftwareDevice


class AttLog:

    def __init__(self, user_id, att_time, ver_type, ver_state):
        self.user_id = user_id
        self.att_time = att_time
        self.ver_type = ver_type
        self.ver_state = ver_state


class PyZKDevice(ZkSoftwareDevice):
    """
        Dispositivo que usa la librería pyzk para conectarse a los relojes de zksoftware
    """

    def __init__(self, ip, port, timezone='America/Argentina/Buenos_Aires'):
        self.ip = ip
        self.port = port
        self.timezone = pytz.timezone(timezone)
        self.zk = ZK(ip, port, timeout=5)
        self.conn = None

    def disconnect(self):
        if self.conn:
            self.conn.disconnect()
            self.conn = None

    def connect(self):
        self.conn = self.zk.connect()

    def enable_device(self):
        self.conn.enable_device()

    def disable_device(self, timer=None):
        self.conn.disable_device()

    def obtener_marcaciones(self):
        marcaciones = []
        atts = self.conn.get_attendance()
        for at in atts:
            """ transformo el objeto """
            user_id = at.user_id
            att_time = at.timestamp
            ver_type = at.status
            ver_state = at.punch
            log = AttLog(user_id,att_time,ver_type,ver_state)
            marcaciones.append(log)
        return marcaciones


    def borrar_marcaciones(self):
        pass    
