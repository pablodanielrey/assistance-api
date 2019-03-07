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

z.read_all_user_id()
z.read_all_fptmp()
z.print_users_summary()
z.read_att_log()
z.print_attlog()

logging.info(z.users)
for u in z.users.values():
    logging.info(u.user_id)
    logging.info(u.user_name)
    logging.info(u.user_password)

z.enable_device()
z.disconnect()
