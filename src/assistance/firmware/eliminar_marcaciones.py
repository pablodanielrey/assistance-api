import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *

"""Elimina las marcaciones existentes en el dispositivo"""

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    z.clear_att_log()

    z.enable_device()
finally:
    z.disconnect()