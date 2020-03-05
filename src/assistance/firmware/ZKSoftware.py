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

class ZKSoftware:
    
    def __init__(self, ip, port, timezone='America/Argentina/Buenos_Aires'):
        self.ip = ip
        self.port = port
        self.timezone = pytz.timezone(timezone)
        self.session_id = 0
        self.reply_number = 0
        self.connected_flg = False

    """
        ----------------------------
        Métodos de la librería
        ----------------------------
    """
    """
        ----------------------------
        Bajo Nivel Creacion de paquetes y envio/recepcion
        ----------------------------
    """
    def _create_packet(self, cmd_code, data=None, session_id=None,
                      reply_number=None):
        """
        Crea un paquete con los datos pasados como parametro.

        :param cmd_code: Int, Command/reply identifier(see defs.py).
        :param data: Bytearray, data to be placed in the data field
        of the payload.
        :param session_id: Int, session id, if not specified, uses
        the session from connection setup.
        :param reply_number: Int, reply counter, if not specified,
        the reply number is obtained from context.
        :return:
        """
        zk_packet = bytearray(START_TAG)  # fixed tag
        zk_packet.extend([0x00] * 2)  # size of payload
        zk_packet.extend([0x00] * 2)  # fixed zeros
        zk_packet.extend(struct.pack('<H', cmd_code))  # cmd code / reply id
        zk_packet.extend([0x00] * 2)  # checksum field

        # append session id
        if session_id is None:
            zk_packet.extend(struct.pack('<H', self.session_id))
        else:
            zk_packet.extend(struct.pack('<H', session_id))

        # append reply number
        if reply_number is None:
            zk_packet.extend(struct.pack('<H', self.reply_number))
        else:
            zk_packet.extend(struct.pack('<H', reply_number))

        # append additional data
        if data:
            zk_packet.extend(data)

        # write size field
        zk_packet[4:6] = struct.pack('<H', len(zk_packet) - 8)
        # write checksum
        zk_packet[10:12] = struct.pack('<H', self._checksum16(zk_packet[8:]))

        return zk_packet    

    def _send_command(self, cmd, data=None):
        """
        Envia un paquete con el comando y los datos asociados si son incluidos

        :param cmd: Integer, command id.
        :param data: Bytearray, data to be placed in the data field
        of the payload.
        :return: None.
        """
        self._send_packet(self._create_packet(cmd, data))

    def _send_packet(self, zkp):
        """
        Envia un paquete completo.

        :param zkp: Bytearray, packet to send.
        :return: None.
        """
        self.soc_zk.send(zkp)
    
    def _recv_packet(self, buff_size=4096):
        """
        Recibe datos desde el dispositivo.

        :param buff_size: Int, maximum amount of data to receive,
        if not specified, is set to 1024.
        :return: Bytearray, received data.
        """
        return bytearray(self.soc_zk.recv(buff_size))

    def _recv_reply(self, buff_size=1024):
        """
        Recibe respuesta desde el dispositivo.
        :param buff_size: Int, maximum amount of data to receive,
        if not specified, is set to 1024, also updates the reply number,
        and stores fields of the packet to the attributes:
        - self.last_reply_code
        - self.last_session_code
        - self.last_reply_counter
        - self.last_payload_data
        :return: Bytearray, received data,
        also stored in last_payload_data.
        """
        zkp = self.soc_zk.recv(buff_size)
        zkp = bytearray(zkp)
        self._parse_ans(zkp)
        self.reply_number += 1

    def _recv_long_reply(self, buff_size=4096):
        """
        Recibe un dataset grande desde el dispositivo.
        
        :param buff_size: Int, maximum amount of data to receive,
        if not specified, is set to 1024.
        :return: Bytearray, received dataset, if the it extract the dataset,
        returns an emtpy bytearray.
        """
        zkp = self._recv_packet(buff_size)
        self._parse_ans(zkp)
        self.reply_number += 1

        dataset = bytearray([])

        if self.last_reply_code == CMD_DATA:
            # device sent the dataset immediately, i.e. short dataset
            dataset = self.last_payload_data

        elif self.last_reply_code == CMD_PREPARE_DATA:
            # seen on fp template download procedure

            # receives first part of the packet with the long dataset
            zkp = self._recv_packet(16)

            # extracts size of the total packet
            total_size = 8 + struct.unpack('<H', zkp[4:6])[0]
            rem_recv = total_size - len(zkp)
            # keeps reading until it receives the complete dataset packet
            while len(zkp) < total_size:
                zkp += self._recv_packet(rem_recv)
                rem_recv = total_size - len(zkp)

            self._parse_ans(zkp)

            dataset = self.last_payload_data

            # receives the acknowledge after the dataset packet
            self._recv_packet(buff_size)

        elif self.last_reply_code == CMD_ACK_OK:
            # device sent the dataset with additional commands, i.e. longer
            # dataset, see ex_data spec
            size_info = struct.unpack('<I', self.last_payload_data[1:5])[0]

            # creates data for "ready for data" command
            rdy_struct = bytearray(4 * [0])
            rdy_struct.extend(struct.pack('<I', size_info))

            self._send_command(CMD_DATA_RDY, data=bytearray(rdy_struct))

            # receives the prepare data reply
            self._recv_packet(24)

            # receives the first part of the packet with the long dataset
            zkp = self._recv_packet(16)

            # extracts size of the total packet
            total_size = 8 + struct.unpack('<H', zkp[4:6])[0]
            rem_recv = total_size - len(zkp)

            # keeps reading until it receives the complete dataset packet
            while len(zkp) < total_size:
                zkp += self._recv_packet(rem_recv)
                rem_recv = total_size - len(zkp)
            self._parse_ans(zkp)
            dataset = self.last_payload_data

            # receives the acknowledge after the dataset packet
            self._recv_packet(buff_size)

            # increment reply number and send "free data" command
            self.reply_number += 1
            self._send_command(CMD_FREE_DATA)

            # receive acknowledge
            self._recv_packet(buff_size)

            # update reply counter
            self.reply_number += 1

        return dataset
    
    def _checksum16(self, payload):
        """
        Calcula el checksum del paquete

        :param payload: Bytearray, data to which the checksum is going
        to be applied.
        :return: Int, checksum result given as a number.
        """
        chk_32b = 0  # accumulates short integers to calculate checksum
        j = 1  # iterates through payload
        # make odd length packet, even
        if len(payload) % 2 == 1:
            payload.append(0x00)
        while j < len(payload):
            # extract short integer, in little endian, from payload
            num_16b = payload[j - 1] + (payload[j] << 8)
            # accumulate
            chk_32b += num_16b
            j += 2  # increment pointer by 2 bytes
        # adds the two first bytes to the other two bytes
        chk_32b = (chk_32b & 0xFFFF) + ((chk_32b & 0xFFFF0000) >> 16)
        # ones complement to get final checksum
        chk_16b = chk_32b ^ 0xFFFF
        return chk_16b

    def _parse_ans(self, zkp):
        """
        Comprueba los campos del paquete, extrae la respuesta, codigo, contador y 
        los guarda en los atributos correspondientes:
        - self.last_reply_code
        - self.last_session_code
        - self.last_reply_counter
        - self.last_payload_data
        :param zkp: Bytearray, packet.
        :return: Bool, returns True if the packet is valid, False otherwise.
        """
        self.last_reply_code = -1
        self.last_session_code = -1
        self.last_reply_counter = -1
        self.last_payload_data = bytearray([])

        # check the start tag
        if not zkp[0:4] == START_TAG:
            print("Bad start tag")
            return False

        # extracts size of packet
        self.last_reply_size = struct.unpack('<I', zkp[4:8])[0]

        # checks the checksum field
        if not self._is_valid_payload(zkp[8:]):
            print("Invalid checksum")
            return False

        # stores the packet fields to the listed attributes

        self.last_packet = zkp

        self.last_reply_code = struct.unpack('<H', zkp[8:10])[0]

        self.last_session_code = struct.unpack('<H', zkp[12:14])[0]

        self.last_reply_counter = struct.unpack('<H', zkp[14:16])[0]

        self.last_payload_data = zkp[16:]
   
    def _is_valid_payload(self, p):
        """
        Comprueba si el contenido del paquete es valido comprobando el checksum.

        :param p: Bytearray, with the payload contents.
        :return: Bool, if the payload is consistent, returns True,
        otherwise returns False.
        """
        # if the checksum is valid the checksum calculation, without removing the
        # checksum, should be equal to zero

        if self._checksum16(p) == 0:
            return True
        else:
            return False

    def _recvd_ack(self):
        """
        Comprueba si la ultima respuesta fue paquete ACK.

        :return: Bool, True if the last reply was an CMD_ACK_OK reply,
        returns False if otherwise.
        """
        if self.last_reply_code == CMD_ACK_OK:
            return True
        else:
            return False
    
    """
        ----------------------------
        Nivel intermedio Seteo de valores en dispositivo
        ----------------------------
    """

    def _set_device_info(self, param_name, new_value):
        """
        Configura en el dispositivo los parametros enviados.

        :param param_name: String, parameter to modify, see the protocol
        terminal spec to see a list of valid param names and valid values.
        :param new_value: String, the new value of the parameters, if it is a
        boolean, it may be given as "0" or "1", integers are given as strings.
        :return: Bool, returns True if the commands were
        processed successfully.
        """
        self._send_command(CMD_OPTIONS_WRQ, bytearray(
            "{0}={1}\x00".format(param_name, new_value), 'ascii'))
        self._recv_reply()
        ack1 = self._recvd_ack()
        self._send_command(CMD_REFRESHOPTION)
        self._recv_reply()
        ack2 = self._recvd_ack()
        return ack1 and ack2
    
    """
        ----------------------------
        Envio de Comandos
        ----------------------------
    """
    def _connect_net(self, ip_addr, dev_port):
        """
        Establece la conexion con el dispositivo, configura el socket e inicia la sesion.
        :param ip_addr: String, ip address of the device.
        :param dev_port: Int, port number.
        :return: Bool, returns True if connection is successful,
        otherwise it returns False, also sets the flag self.connected_flg if
        the connection is successful.
        """

        # connects to machine
        self.soc_zk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_zk.connect((ip_addr, dev_port))

        # send connect command
        self._send_command(CMD_CONNECT)

        # receive reply
        self._recv_reply()

        # sets session id
        self.session_id = self.last_session_code

        # set SDKBuild variable of the device
        self._set_device_info('SDKBuild', '1')

        # check reply code
        self.connected_flg = self._recvd_ack()
        return self.connected_flg

    def disconnect(self):
        """
        Termina la conexion previamente abierta.
        :return: Bool, returns True if disconnection command was
        processed successfully, also clears the flag self.connected_flg.
        """
        # terminate connection command
        self._send_command(CMD_EXIT)
        self._recv_reply()

        # close connection and update flag
        self.soc_zk.close()
        self.connected_flg = False

        return self._recvd_ack()
    
    def connect(self):
        self._connect_net(self.ip, self.port)

    def enable_device(self):
        """
        Activa el dispositivo.
        :return: Bool, returns True if the device acknowledges
        the enable command.
        """
        self._send_command(CMD_ENABLEDEVICE)
        self._recv_reply()
        return self._recvd_ack()

    def disable_device(self, timer=None):
        """
        Desactiva el dispositivo, huellas, teclado, y modulo RF.
        :param timer: Integer, disable timer, if it is omitted, an enable
        command must be send to make the device return to normal operation.
        :return: Bool, returns True if the device acknowledges
        the disable command.
        """
        if timer:
            self._send_command(CMD_DISABLEDEVICE, struct.pack('<I', timer))
        else:
            self._send_command(CMD_DISABLEDEVICE)

        self._recv_reply()
        return self._recvd_ack()
    
    def _refresh_data(self):
        """
        Refresh data on device (fingerprints, user info and settings).

        :return: None.
        """
        self._send_command(cmd=CMD_REFRESHDATA)
        self._recv_reply()

    def _clear_att_log(self):
        """
        Delete the attendance log record on the machine.

        :return: None.
        """
        self._send_command(cmd=CMD_CLEAR_ATTLOG)
        self._recv_reply()
        self._refresh_data()
    
    """
        ----------------------------
        Codificadores / Decodificadores
        ----------------------------
    """    
    def _decode_time(self, enc_t_arr):
        """
        Decodifica el tiempo de Bytearray (Segun especificacion de ZK) a datetime.
        :param enc_t_arr: Bytearray, with the time field stored in little endian.
        :return: Datetime object, with the extracted date.
        """
        
        """
        ------------------- Libreria Original ------------------------------
        enc_t = struct.unpack('<I', enc_t_arr)[0]  # extracts the time value
        secs = int(enc_t % 60)  # seconds
        mins = int((enc_t / 60.) % 60)  # minutes
        hour = int((enc_t / 3600.) % 24)  # hours
        day = int(((enc_t / (3600. * 24.)) % 31)) + 1  # day
        month = int(((enc_t / (3600. * 24. * 31.)) % 12)) + 1  # month
        year = int((enc_t / (3600. * 24.)) / 365) + 2000  # year
        return datetime.datetime(year, month, day, hour, mins, secs)
        ------------------- Correccion Temporal ----------------------------
        enc_t = struct.unpack('<I', enc_t_arr)[0]  # extracts the time value
        fecha_inicio = datetime.datetime(1999, 8, 19, 0, 0)
        delta = datetime.timedelta(seconds=enc_t)
        resultado = fecha_inicio + delta
        -------------------- Ultima Correccion -----------------------------
        """
        t = struct.unpack("<I", enc_t_arr)[0]
        second = t % 60
        t = t // 60

        minute = t % 60
        t = t // 60

        hour = t % 24
        t = t // 24

        day = t % 31 + 1
        t = t // 31

        month = t % 12 + 1
        t = t // 12

        year = t + 2000

        d = datetime.datetime(year, month, day, hour, minute, second)
        return d

    def _decodificar_str(self, s):
        """Retorna la cadena hasta el primer valor invalido"""
        i = 0
        while i < len(s) and s[i] != 0x00:
            i += 1
        return s[:i]
    
    """
        ----------------------------
        Obtencion de datos
        ----------------------------
    """   
    def _read_att_log(self):
        """
        Obtiene los logs del dispositivo y los decodifica.

        :return: None. Stores the attendance log entries
        in the att_log attribute.
        """
        self._send_command(cmd=CMD_DATA_WRRQ, data=bytearray.fromhex('010d000000000000000000'))
        datos = self._recv_long_reply()

        att_logs = []

        try:    
            # Obtiene numero de registros
            att_count = struct.unpack('<H', datos[0:2])[0]/40
            att_count = int(att_count)
        except:
            # Cado donde no hay marcaciones y da error el tamaño de buffer
            att_count = 0

        # Se saltea el tamaño de los logs y zeros
        i = 4

        # Saco datos de cada uno de los registros
        for idx in range(att_count):
            (user_sn, user_id, ver_type, att_time, ver_state) = struct.unpack('<H9s15xBIB8x', datos[i:i+40])
            # Correccion de datos
            user_id = self._decodificar_str(user_id).decode('ascii')
            att_time = self._decode_time(self.last_payload_data[i+27:i+31])
            # Creacion de Attlog
            log = AttLog(user_id,att_time,ver_type,ver_state)
            # Guarda el log
            att_logs.append(log)
            i += 40
        return att_logs

    
    """
        Metodos Publicos
    """

    def obtener_marcaciones(self):
        """
        Devuelve las marcaciones registradas en el dispositivo como un json de logs.

        """
        return self._read_att_log()
        """
        datos = []
        for l in att_log:
            #pDate = datetime.datetime.strptime(l.att_time,'%Y-%m-%d %H:%M:%S').replace(microsecond=0,tzinfo=None)
            pDate = l.att_time.replace(microsecond=0,tzinfo=None)
            zpDate = self.timezone.localize(pDate)
            #zpDate = datetime.datetime.strftime(zpDate,'%Y-%m-%d %H:%M:%S')
            d = {
                'PIN':l.user_id,
                'DateTime': zpDate,
                'Verified':l.ver_type,
                'WorkCode':l.ver_state
            }
            datos.append(d)

        return datos
        """

    def borrar_marcaciones(self):
        """
        Elimina el registro de marcaciones en el dispositivo.

        :return: None.
        """
        self._clear_att_log()
