import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
from ZKSoftware import *
import logging
logging.getLogger().setLevel(logging.INFO)

"""Template de pruebas"""

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()
    ##################Comandos a probar ########################
    
    #usuarios = leer_usuarios(z)
    huellas = leer_huellas(z)
    logging.info(huellas) 

    ############################################################
    z.enable_device()
finally:
    z.disconnect()