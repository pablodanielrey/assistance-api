import struct

def ser_user(user_sn, user_id, admin_level, enabled, user_password, user_name, card_number, user_group, user_tzs):
    """
    Builds user entry.
    :return: Bytearray, with the users info.
    """
    user_info = bytearray([0x00] * 72)
    user_info[0:2] = struct.pack('<H', user_sn)
    user_info[2] = (admin_level << 1) | not enabled
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
    
def _decodeBytearray(dato):
    return binascii.hexlify(dato).decode('ascii')