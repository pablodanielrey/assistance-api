import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
from ZKSoftware import *

"""Template de pruebas"""

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()
    ##################Comandos a probar ########################
    
    leer_todos_usuarios_id(z)

    ############################################################
    z.enable_device()
finally:
    z.disconnect()