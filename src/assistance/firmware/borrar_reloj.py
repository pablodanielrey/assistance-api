import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *

"""Elimina todos los datos del reloj"""

ip_address = '163.10.56.25'
machine_port = 4370

print("ATENCION!!! ESTE PROCEDIMIENTO ELIMINA TODOS LOS DATOS DEL RELOJ.")
print("ATENCION!!! ELIMINARA DATOS DEL RELOJ CON IP: {}".format(ip_address))
respuesta = input("ESTA SEGURO? S/n: ")
if respuesta == 'S':
    print('ELIMINANDO DATOS...')
    z = pyzk.ZKSS()
    try:
        z.connect_net(ip_address, machine_port)
        z.disable_device()
        z.clear_data()
        z.enable_device()
    finally:
        z.disconnect()
    print('PROCESO TERMINADO.')
else:
    print('NO SE HA BORRADO EL RELOJ')




