import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
import binascii
logging.getLogger().setLevel(logging.INFO)

def _decodeBytearray(dato):
    return binascii.hexlify(dato).decode('ascii')

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
z.connect_net(ip_address, machine_port)
z.disable_device()

z.read_all_user_id()
z.read_all_fptmp()

datos = {}
datos['usuarios'] = []
for u in z.users.values():
    huellas = []
    contador = 0
    for h,f in u.user_fptmps:
        if h != 0:
            huella = _decodeBytearray(h)
        else:
            huella = 0
        huellas.append({
            'dedo' : contador,
            'huella' : huella,
            'flag' : f
        })
        contador += 1
    datos['usuarios'].append({
        'usuario': u.user_id,
        'password': u.user_password,
        'admin_level': u.admin_level,
        'activado': u.not_enabled,
        'huellas': huellas
    })

with open('/tmp/usuarios.json', 'w') as outfile:
    json.dump(datos, outfile)

z.enable_device()
z.disconnect()