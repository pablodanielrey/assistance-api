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

z.read_att_log()

datos = {}
datos['logs'] = []
for l in z.att_log:
    print("User: {} Marcacion: {}".format(l.user_id, l.att_time))
    datos['logs'].append({
            'usuario' : l.user_id,
            'tipo' : l.ver_type,
            'marcacion' : '{}'.format(l.att_time),
            'estado' : l.ver_state
    })

with open('/tmp/logs.json', 'w') as outfile:
    json.dump(datos, outfile)

z.enable_device()
z.disconnect()