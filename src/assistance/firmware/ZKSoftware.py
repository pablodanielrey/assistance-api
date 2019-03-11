import struct
import binascii
import logging
logging.getLogger().setLevel(logging.INFO)


"""Codigo comun de ayuda y pruebas para propia implementacion de funciones de zk"""

def decodeBytearray(dato):
    return binascii.hexlify(dato).decode('ascii')

def encodeBytearray(dato):
    return binascii.unhexlify(dato)

def empaquetar_usuario(user_sn, user_id, admin_level, not_enabled, user_password,
 user_name='', card_number=0, user_group=1, user_tzs=[]):
    """
    Builds user entry.
    :return: Bytearray, with the users info.
    """
    user_info = bytearray([0x00] * 72)
    user_info[0:2] = struct.pack('<H', user_sn)
    user_info[2] = (admin_level << 1) | not_enabled
    user_info[3:3+len(user_password)] = user_password.encode()
    user_info[11:11+len(user_name)] = user_name.encode()
    user_info[35:39] = struct.pack('<I', card_number)
    user_info[39] = user_group

    if len(user_tzs) != 0:
        user_info[40:42] = bytes([1, 0])
        user_info[42:44] = struct.pack('<H', user_tzs[0])
        user_info[44:46] = struct.pack('<H', user_tzs[1])
        user_info[46:48] = struct.pack('<H', user_tzs[2])

    user_info[48:48 + len(user_id)] = user_id.encode()
    return user_info

def subir_info_usuario(z,user_sn, user_info=None):
    """
    Sube la informacion del usuario pasado como parametro.
    :return: None.
    """
    if user_info == None:
        print('Salteo de usuario sin info')
    else:
        z.send_command(cmd=0x0008, data=user_info)
        z.recv_reply()
        z.refresh_data()

def subir_huella(z, user_sn, fp, fp_index, fp_flag):
    """
    Upload fingerprint template data of a given user.
    :param user_id: String, user's ID.
    :param fp: Bytearray, fingerprint template.
    :param fp_index: Integer, fingerprint index.
    :param fp_flag: Integer, fingerprint flag (duress=3, valid=1).
    :return: None.
    """
    z.disable_device()

    # sending prep struct
    fp_size = struct.pack('<H', len(fp))
    prep_data = bytearray([0x00]*4)
    prep_data[0:2] = fp_size
    z.send_command(cmd=0x05dc, data=prep_data)
    z.recv_reply()

    # sending template
    z.send_command(cmd=0x05dd, data=fp)
    z.recv_reply()

    # request checksum
    z.send_command(cmd=0x0077)
    z.recv_reply()  # ignored

    # send write request
    tmp_wreq_data = bytearray([0x00] * 6)
    tmp_wreq_data[0:2] = struct.pack('<H', user_sn)
    tmp_wreq_data[2] = fp_index
    tmp_wreq_data[3] = fp_flag
    tmp_wreq_data[4:6] = fp_size
    z.send_command(cmd=0x0057, data=tmp_wreq_data)
    z.recv_reply()

    # free data buffer
    z.send_command(cmd=0x05de)
    z.recv_reply()

    # refresh data
    z.refresh_data()



def decodificar_str(s):
    i = 0
    while i < len(s) and s[i] != 0x00:
        i += 1
    return s[:i]

def decodificar_info_usuario(data):
    (sn,permission, passw, name, card, group, tz, tz1, tz2, tz3, uid) = struct.unpack('<HB8s24sIBHHHH9s15x',data)
    return {
        'sn': sn,
        'permission': permission,
        'password': passw.decode('ascii'),
        'name': name.decode('ascii'),
        'card': card,
        'group': group,
        'tz': tz,
        'tz1': tz1,
        'tz2': tz2,
        'tz3': tz3,
        'uid': decodificar_str(uid).decode('ascii')
    }



def leer_todos_usuarios_id(z):
    """
    Requests all the users info, except the fingerprint templates.
    :return: None. Stores the users info in the ZKUsers dict.
    """
    z.send_command(cmd=0x05df, data=bytearray.fromhex('0109000500000000000000'))

    # receive dataset with users info
    users_dataset = z.recv_long_reply()
    total_size_dataset = len(users_dataset)

    # clear the users dict
    z.users = {}

    # skip first 4 bytes (size + zeros)
    i = 4
    while i < total_size_dataset:
        datos = users_dataset[i:i+72]
        usuario = decodificar_info_usuario(datos)
        i = i + 72
        logging.info(usuario)

        """
        #print(users_dataset[i:i+72])
        # extract serial number
        user_sn = struct.unpack('<H', users_dataset[i:i+2])[0]

        # extract permission token
        perm_token = users_dataset[i+2]

        # extract user password, if it is invalid, stores ''
        if users_dataset[i+3] != 0x00:
            password = users_dataset[i + 3:i + 11]
            # remove trailing zeros
            password = password.decode('ascii').replace('\x00', '')

        else:
            password = ''

        # extract user name
        user_name = users_dataset[i+11:i+35].decode('ascii')

        # remove non printable chars
        user_name = user_name.replace('\x00', '')

        # extract card number
        card_no = struct.unpack('<I', users_dataset[i+35:i+39])[0]

        # extract group number
        group_no = users_dataset[i+39]

        # extract user timezones if they exists
        if struct.unpack('<H', users_dataset[i+40:i+42])[0] == 1:
            user_tzs = [0]*3
            user_tzs[0] = struct.unpack('<H', users_dataset[i+42:i+44])[0]
            user_tzs[1] = struct.unpack('<H', users_dataset[i+44:i+46])[0]
            user_tzs[2] = struct.unpack('<H', users_dataset[i+46:i+48])[0]
        else:
            user_tzs = []

        # extract the user id
        user_id = users_dataset[i+48:i+57].decode('ascii')
        prueba = struct.unpack('<H', users_dataset[i+48:i+57])
        print("User Id: {}".format(user_id))
        print('Data Set de user_id: {}'.format(users_dataset[i+48:i+57]))
        
        # remove non printable chars
        user_id = user_id.replace('\x00', '')
        # every user entry is 72 bytes long
        i += 72
        """