import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
from ZKSoftware import *

"""Obtiene la lista de usuarios que estan creados en el reloj biometrico y sus huellas"""

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    z.read_op_log()
    z.print_oplog()

    z.enable_device()
finally:
    z.disconnect()