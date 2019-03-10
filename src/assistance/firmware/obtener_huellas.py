import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
from ZKSoftware import *
logging.getLogger().setLevel(logging.INFO)

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    z.read_all_user_id()
    z.read_all_fptmp()

    datos = {}
    for u in z.users.values():
        huellas = []
        contador = 0
        for h,f in u.user_fptmps:
            if h != 0:
                huella = decodeBytearray(h)
            else:
                huella = 0
            huellas.append({
                'dedo' : contador,
                'huella' : huella,
                'flag' : f
            })
            contador += 1
        datos[u.user_id] = {
            'huellas' : huellas,
        }

    with open('/tmp/huellas.json', 'w') as outfile:
        json.dump(datos, outfile)

    z.enable_device()
finally:
    z.disconnect()

