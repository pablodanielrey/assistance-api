import time
import os.path
#import pyzk.pyzk as pyzk
#from pyzk.zkmodules.defs import *
from ZKSoftware import ZKSoftware
import logging
import json
logging.getLogger().setLevel(logging.INFO)

"""Obtiene las marcaciones que estan almacenadas en el reloj biometrico"""

ip_address = '163.10.56.204'
machine_port = 4370

z = ZKSoftware(ip_address, machine_port)
#z = pyzk.ZKSS()
try:    
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    #La funcion read_att_log da error cuando no puede obtener marcaciones por lo tanto creé una "Contencion" del error
    try:
        z.read_att_log()
    except:
        pass

    datos = {}
    datos['logs'] = []
    for l in z.att_log:
        print('Usuario: {} Marcacion: {}'.format(l.user_id,l.att_time))
        datos['logs'].append({
                'usuario' : l.user_id,
                'tipo' : l.ver_type,
                'marcacion' : '{}'.format(l.att_time),
                'estado' : l.ver_state
        })

    with open('/tmp/logs.json', 'w') as outfile:
        json.dump(datos, outfile)
        
    z.enable_device()
finally:
    z.disconnect()