import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
logging.getLogger().setLevel(logging.INFO)


ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
z.connect_net(ip_address, machine_port)
z.disable_device()

z.read_all_user_id()
z.print_users_summary()

datos = {}
datos['usuarios'] = []
for u in z.users.values():
    datos['usuarios'].append({
        'usuario': u.user_id,
        'password': u.user_password,
        'admin_level': u.admin_level,
        'activado': u.not_enabled,
    })

with open('/tmp/usuarios.json', 'w') as outfile:
    json.dump(datos, outfile)


z.enable_device()
z.disconnect()