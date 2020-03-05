import struct
import binascii
import logging
import base64
import hashlib
logging.getLogger().setLevel(logging.INFO)

"""Codigo comun de ayuda y pruebas para propia implementacion de funciones de zk"""

def decodeBytearray(dato):
    return binascii.hexlify(dato).decode('ascii')

def encodeBytearray(dato):
    return binascii.unhexlify(dato)

def decodeBytearrayBase64(dato):
    """Transforma bytes a string base64 para almacenar"""
    return binascii.b2a_base64(dato, newline=False).decode('ascii')

def encodeBytearrayBase64(dato):
    """Transforma base64 a bytes para enviar"""
    retorno = binascii.a2b_base64(dato.encode('ascii'))
    print(retorno)
    return retorno

def decodificar_str(s):
    """Corta la cadena hasta el primer valor invalido"""
    i = 0
    while i < len(s) and s[i] != 0x00:
        i += 1
    return s[:i]

def decodificar_info_usuario(data):
    """Retorna diccionario de usuario decodificado desde bytes"""
    (sn,permission, passw, name, card, group, tz, tz1, tz2, tz3, uid) = struct.unpack('<HB8s24sIBHHHH9s15x',data)
    return {
        'user_sn': sn,
        'permission_token': permission,
        'user_password': decodificar_str(passw).decode('ascii'),
        'user_name': decodificar_str(name).decode('ascii'),
        'card_number': card,
        'user_group': group,
        'user_tz': tz,
        'user_tz1': tz1,
        'user_tz2': tz2,
        'user_tz3': tz3,
        'user_id': decodificar_str(uid).decode('ascii')
    }

def leer_usuarios(z):
    """
    Retetorna todos los datos de los usuarios desde el reloj excepto las huellas
    :return: Arreglo de usuarios.
    """
    usuarios = []

    z.send_command(cmd=0x05df, data=bytearray.fromhex('0109000500000000000000'))

    # recibe los datos de la consulta realizada con el comando anterior
    users_dataset = z.recv_long_reply()
    total_size_dataset = len(users_dataset)

    # saltea primeros 4 bytes (size + zeros)
    i = 4
    while i < total_size_dataset:
        datos = users_dataset[i:i+72]
        usuario = decodificar_info_usuario(datos)
        usuarios.append(usuario)
        
        #Saltea a siguiente usuario
        i = i + 72
    
    return usuarios

def leer_huellas(z):
    """
    Retorna todas las huellas de los usuarios.
    :return: Arreglo de huellas.
    """
    huellas = {}

    z.send_command(cmd=0x05df, data=bytearray.fromhex('0107000200000000000000'))

    # recibe los datos de la consulta realizada con el comando anterior
    fptemplates_dataset = z.recv_long_reply()
    total_size_dataset = len(fptemplates_dataset)

    # saltea primeros 4 bytes (size + zeros)
    i = 4
    while i < total_size_dataset:
        # Calcula tamaño de datos
        tmp_size = struct.unpack('<H', fptemplates_dataset[i:i + 2])[0] \
                       - 6
        
        (user_sn, fp_idx, fp_flg) = struct.unpack('<HBB',fptemplates_dataset[i+2:i+6])
        fp = fptemplates_dataset[i + 6: i + tmp_size]
        if user_sn in huellas.keys(): 
            huellas[user_sn].append({
                'fp_idx': fp_idx,
                'fp': decodeBytearray(fp),
                'fp_hash': hashlib.md5(fp).hexdigest(),
                'fp_flag': fp_flg        
            })
        else:
            huellas[user_sn] = []
            huellas[user_sn].append({
                'fp_idx': fp_idx,
                'fp': decodeBytearray(fp),
                'fp_hash': hashlib.md5(fp).hexdigest(),
                'fp_flag': fp_flg        
            })
                        
        # Saltea a siguiente huella
        i += tmp_size+6
    return huellas


    """
    Para hacer funcionar el metodo read_all_user_id solo hace falta reemplazar el metodo por este otro que corrige el problema de los datos erroneos en strings
    
    def _decodificar_str(self,s):
        '''Corta la cadena hasta el primer valor invalido'''
        i = 0
        while i < len(s) and s[i] != 0x00:
            i += 1
        return s[:i]
    
    def read_all_user_id(self):
        '''
        Requests all the users info, except the fingerprint templates.

        :return: None. Stores the users info in the ZKUsers dict.
        '''
        self.send_command(cmd=CMD_DATA_WRRQ,
                          data=bytearray.fromhex('0109000500000000000000'))

        # receive dataset with users info
        users_dataset = self.recv_long_reply()
        total_size_dataset = len(users_dataset)

        # clear the users dict
        self.users = {}

        # skip first 4 bytes (size + zeros)
        i = 4
        while i < total_size_dataset:
            (user_sn,perm_token, password, user_name, card_no, group_no, tz, tz1, tz2, tz3, user_id) = struct.unpack('<HB8s24sIBHHHH9s15x',users_dataset[i:i+72])
            
            password = self._decodificar_str(password).decode('ascii')
            user_name = self._decodificar_str(user_name).decode('ascii')
            user_id = self._decodificar_str(user_id).decode('ascii')
            if tz == 1:
                user_tzs = [0]*3
                user_tzs[0] = tz1
                user_tzs[1] = tz2
                user_tzs[2] = tz3
            else:
                user_tzs = []
            
            
            # append user to the list of users
            self.add_user(user_sn)
            # set the corresponding info
            self.users[user_sn].set_user_info(
                                            user_id=user_id,
                                            user_sn=user_sn,
                                            name=user_name,
                                            password=password,
                                            card_no=card_no,
                                            admin_lv=perm_token >> 1,
                                            neg_enabled=perm_token & 1,
                                            user_group=group_no,
                                            user_tzs=user_tzs
                                            )
            # every user entry is 72 bytes long
            i += 72
    """