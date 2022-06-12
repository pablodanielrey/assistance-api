import time
import os.path
from pyzk.zkmodules.defs import *
import json
from assistance.firmware.ZKSoftware import ZKSoftware

"""Obtiene las marcaciones que estan almacenadas en el reloj biometrico"""

ip_address = '163.10.56.25'
machine_port = 4370

z = ZKSoftware(ip_address,machine_port)
z.connect()
try:
    marcaciones = z.obtener_marcaciones()
finally:
    z.disconnect()

for m in marcaciones:
    print(f"DNI: {m.user_id} - MARCACION: {m.att_time} - TIPO: {m.ver_type} - ESTADO: {m.ver_state}")
