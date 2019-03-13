import pytz

class AttLog:
    def __init__(self):
        self.user_id = ''
        self.att_time = ''
        self.ver_type = ''
        self.ver_state = ''



class ZKSoftware:
    
    def __init__(self, ip, port, timezone='America/Argentina/Buenos_Aires'):
        self.ip = ip
        self.port = port
        self.timezone = pytz.timezone(timezone)

    """
        ----------------------------
        los métodos de la librería
    """

    def _disconnect():
        pass

    def _connect_net(ip, port):
        pass

    def disable_device():
        pass

    def enable_device():
        pass

    def _read_att_log():
        return [AttLog()]

    """
        -----------------------------
    """

    def obtener_marcaciones(self):
        try:    
            self._connect_net(ip_address, machine_port)
            self.disable_device()

            #La funcion read_att_log da error cuando no puede obtener marcaciones por lo tanto creé una "Contencion" del error
            att_log = self._read_att_log()
            datos = {}
            datos['logs'] = []
            for l in att_log:
                pDate = datetime.datetime.strptime(l.att_time,'%Y-%m-%d %H:%M:%S').replace(microsecond=0,tzinfo=None)
                zpDate = self.timezone.localize(pDate)
                d = {
                    'PIN':l.user_id,
                    'DateTime': zpDate,
                    'Verified':l.ver_type
                    'Status':l.estado,
                    'WorkCode':l.ver_state
                }
                datos.append(d)            

            self.enable_device()
        
        finally:
            self._disconnect()

        return datos        