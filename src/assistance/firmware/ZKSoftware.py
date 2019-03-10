import struct
import binascii

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