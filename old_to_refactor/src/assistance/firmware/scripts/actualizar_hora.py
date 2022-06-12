import time
from datetime import datetime, timezone
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import ntplib
import logging
logging.getLogger().setLevel(logging.INFO)

"""Actualiza hora del dispositivo"""

ip_address = '163.10.56.25'
machine_port = 4370

c = ntplib.NTPClient()
respuesta = c.request('2.ar.pool.ntp.org', version=3)
respuesta.offset 
horaNTP = datetime.fromtimestamp(respuesta.tx_time)
horaNTP = horaNTP

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()
    print("Hora NTP actual:     {}".format(horaNTP))
    print("Hora en dispositivo: {}".format(z.get_device_time()))
    print("Actualizando Hora...")
    z.set_device_time(horaNTP)
    print("Hora en dispositivo: {}".format(z.get_device_time()))
    
    z.enable_device()
finally:
    z.disconnect()


