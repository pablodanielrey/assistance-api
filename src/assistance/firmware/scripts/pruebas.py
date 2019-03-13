import time
import os.path
import json
import hashlib
import base64

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
    
    z.read_all_user_id()
    z.read_all_fptmp()
    z.print_users_summary()
    z.read_att_log()
    z.print_attlog()
    ############################################################
    z.enable_device()
finally:
    z.disconnect()