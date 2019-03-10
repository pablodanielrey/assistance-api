import time
from datetime import datetime
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
logging.getLogger().setLevel(logging.INFO)

"""Actualiza hora del dispositivo"""

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    print("Hora en dispositivo: {}".format(z.get_device_time()))
    print("Hora actualizada:    {}".format(datetime.now()))
    print("Actualizando Hora...")
    z.set_device_time(datetime.now())
    print("Hora en dispositivo: {}".format(z.get_device_time()))
    
    z.enable_device()
finally:
    z.disconnect()


