import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
logging.getLogger().setLevel(logging.INFO)


ip_address = '163.10.56.204'
machine_port = 4370

z = pyzk.ZKSS()
z.connect_net(ip_address, machine_port)
z.disable_device()
#z.disconnect()


