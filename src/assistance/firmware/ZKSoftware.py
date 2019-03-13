import pytz
from defs import *

class AttLog:
    def __init__(self,user_id,att_time,ver_type,ver_state):
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

    def decode_time(enc_t_arr):
        """
        Decodes time, as given on ZKTeco get/set time commands.
        :param enc_t_arr: Bytearray, with the time field stored in little endian.
        :return: Datetime object, with the extracted date.
        """
        enc_t = struct.unpack('<I', enc_t_arr)[0]  # extracts the time value
        secs = int(enc_t % 60)  # seconds
        mins = int((enc_t / 60.) % 60)  # minutes
        hour = int((enc_t / 3600.) % 24)  # hours
        day = int(((enc_t / (3600. * 24.)) % 31)) + 1  # day
        month = int(((enc_t / (3600. * 24. * 31.)) % 12)) + 1  # month
        year = int((enc_t / (3600. * 24.)) / 365) + 2000  # year

        return datetime.datetime(year, month, day, hour, mins, secs)

    def _decodificar_str(s):
        """Corta la cadena hasta el primer valor invalido"""
        i = 0
        while i < len(s) and s[i] != 0x00:
            i += 1
        return s[:i]

    def send_command(cmd, data):
        pass

    def recv_long_reply(self, buff_size=4096):
        """
        Receives a large dataset from the device.
        :param buff_size: Int, maximum amount of data to receive,
        if not specified, is set to 1024.
        :return: Bytearray, received dataset, if the it extract the dataset,
        returns an emtpy bytearray.
        """
        zkp = self.recv_packet(buff_size)
        self.parse_ans(zkp)
        self.reply_number += 1

        dataset = bytearray([])

        if self.last_reply_code == CMD_DATA:
            # device sent the dataset immediately, i.e. short dataset
            dataset = self.last_payload_data

        elif self.last_reply_code == CMD_PREPARE_DATA:
            # seen on fp template download procedure

            # receives first part of the packet with the long dataset
            zkp = self.recv_packet(16)

            # extracts size of the total packet
            total_size = 8 + struct.unpack('<H', zkp[4:6])[0]
            rem_recv = total_size - len(zkp)
            # keeps reading until it receives the complete dataset packet
            while len(zkp) < total_size:
                zkp += self.recv_packet(rem_recv)
                rem_recv = total_size - len(zkp)

            self.parse_ans(zkp)

            dataset = self.last_payload_data

            # receives the acknowledge after the dataset packet
            self.recv_packet(buff_size)

        elif self.last_reply_code == CMD_ACK_OK:
            # device sent the dataset with additional commands, i.e. longer
            # dataset, see ex_data spec
            size_info = struct.unpack('<I', self.last_payload_data[1:5])[0]

            # creates data for "ready for data" command
            rdy_struct = bytearray(4 * [0])
            rdy_struct.extend(struct.pack('<I', size_info))

            self.send_command(CMD_DATA_RDY, data=bytearray(rdy_struct))

            # receives the prepare data reply
            self.recv_packet(24)

            # receives the first part of the packet with the long dataset
            zkp = self.recv_packet(16)

            # extracts size of the total packet
            total_size = 8 + struct.unpack('<H', zkp[4:6])[0]
            rem_recv = total_size - len(zkp)

            # keeps reading until it receives the complete dataset packet
            while len(zkp) < total_size:
                zkp += self.recv_packet(rem_recv)
                rem_recv = total_size - len(zkp)
            self.parse_ans(zkp)
            dataset = self.last_payload_data

            # receives the acknowledge after the dataset packet
            self.recv_packet(buff_size)

            # increment reply number and send "free data" command
            self.reply_number += 1
            self.send_command(CMD_FREE_DATA)

            # receive acknowledge
            self.recv_packet(buff_size)

            # update reply counter
            self.reply_number += 1

        return dataset

    def disable_device():
        pass

    def enable_device():
        pass
    
    def _read_att_log():
        """
        Requests the attendance log.
        :return: None. Stores the attendance log entries
        in the att_log attribute.
        """
        self.send_command(cmd=CMD_DATA_WRRQ, data=bytearray.fromhex('010d000000000000000000'))
        self.recv_long_reply()

        att_log = []

        # Obtiene numero de registros
        att_count = struct.unpack('<H', self.last_payload_data[0:2])[0]/40
        att_count = int(att_count)

        # Se saltea el tamaño de los logs y zeros
        i = 4

        # Saco datos de cada uno de los registros
        for idx in range(att_count):
            (user_sn, user_id, ver_type, att_time, ver_state) = struct.unpack('<H9s15xBIB8x', self.last_payload_data[i:i+40])
            # user internal index
            user_sn = 
            # user id
            user_id = self.last_payload_data[i+2:i+11].decode('ascii').\
                replace('\x00', '')
            # verification type
            ver_type = self.last_payload_data[i+26]
            # time of the record
            att_time = decode_time(self.last_payload_data[i+27:i+31])
            # verification state
            ver_state = self.last_payload_data[i+31]
            log = AttLog(user_id,att_time,ver_type,ver_state)
            # append attendance entry
            att_log.append(log)

            i += 40
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
                    'DateTime': l.att_time,
                    'Verified':l.ver_state,
                    'Status':l.estado,
                    'WorkCode':l.ver_state
                }
                datos.append(d)            

            self.enable_device()
        
        finally:
            self._disconnect()

        return datos        