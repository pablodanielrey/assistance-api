import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
logging.getLogger().setLevel(logging.INFO)


ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
z.connect_net(ip_address, machine_port)
z.disable_device()

z.read_att_log()
z.print_attlog()

for u in z.att_log:
    for l in u:
        print("User: {} Marcacion: {}".format(user_id,att_time))

z.enable_device()
z.disconnect()