import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
import hashlib
from ZKSoftware import *
logging.getLogger().setLevel(logging.INFO)

"""Obtiene la lista de usuarios que estan creados en el reloj biometrico y sus huellas usando personalizacion de obtencion"""

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    usuarios = leer_usuarios(z)
    huellas = leer_huellas(z)

    datos = {}
    datos['usuarios'] = []
    for u in usuarios:
        huellas_usuario = []
        if u['user_sn'] in huellas.keys():
            for h in huellas[u['user_sn']]:
                huellas_usuario.append({
                    'fp_index' : h['fp_idx'],
                    'fp' : h['fp'],
                    'fp_hash' : h['fp_hash'],
                    'fp_flag' : h['fp_flag']
                })
        datos['usuarios'].append({
            'user_sn': u['user_sn'],
            'user_id': u['user_id'],
            'user_name': u['user_name'],
            'user_password': u['user_password'],
            'card_number': u['card_number'],
            'admin_level': u['permission_token'] >> 1,
            'not_enabled': u['permission_token'] & 1,
            'user_group': u['user_group'],
            'user_tzs': [u['user_tz1'],u['user_tz2'],u['user_tz3']],
            'huellas': huellas_usuario
        })

    with open('/tmp/usuarios.json', 'w') as outfile:
        json.dump(datos, outfile)
    
    z.enable_device()
finally:
    z.disconnect()