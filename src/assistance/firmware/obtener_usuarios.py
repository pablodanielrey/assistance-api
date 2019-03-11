import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
import hashlib
from ZKSoftware import *
logging.getLogger().setLevel(logging.INFO)

"""Obtiene la lista de usuarios que estan creados en el reloj biometrico y sus huellas"""

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    z.read_all_user_id()
    z.read_all_fptmp()
    z.print_users_summary()

    datos = {}
    datos['usuarios'] = []
    for u in z.users.values():
        print('Usuario ID: {}'.format(u.user_id))
        print('Usuario ID: {}'.format(u.user_id))
        print('Usuario ID: {}'.format(u.user_id))
        huellas = []
        contador = 0
        for h,f in u.user_fptmps:
            if h != 0:
                huella = decodeBytearray(h)
                hashHuella = hashlib.md5(h).hexdigest()
            else:
                huella = 0
                hashHuella = None
            huellas.append({
                'fp_index' : contador,
                'fp' : huella,
                'hashFp' : hashHuella,
                'fp_flag' : f
            })
            contador += 1
        datos['usuarios'].append({
            'user_sn': u.user_sn,
            'user_id': u.user_id,
            'user_name': u.user_name,
            'user_password': u.user_password,
            'card_number': u.card_number,
            'admin_level': u.admin_level,
            'not_enabled': u.not_enabled,
            'user_group': u.user_group,
            'user_tzs': u.user_tzs,
            'huellas': huellas
        })

    with open('/tmp/usuarios.json', 'w') as outfile:
        json.dump(datos, outfile)

    z.enable_device()
finally:
    z.disconnect()