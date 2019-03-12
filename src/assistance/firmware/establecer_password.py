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

"""Borra la contraseña del usuario y estabelece una nueva"""

ip_address = '163.10.56.25'
machine_port = 4370
user_id = '2'
password = '3333'

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    assert(len(password) <= 8)
    #Leo todos los usuarios disponibles
    z.read_all_user_id()
    #Borro la password del usuario
    z.clear_password(user_id)
    #Seteo de nueva pass
    z.set_password(user_id, password)

    z.enable_device()
finally:
    z.disconnect()