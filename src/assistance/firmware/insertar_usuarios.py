import sys
import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
import binascii
logging.getLogger().setLevel(logging.INFO)

def _encodeBytearray(dato):
    return binascii.unhexlify(dato)

ip_address = '163.10.56.25'
machine_port = 4370
try:
    with open('/tmp/usuarios.json','r') as f:
        usuarios = json.load(f)
except Exception as e:
    print('Error: {}'.format(e))
    sys.exit(1)

z = pyzk.ZKSS()
z.connect_net(ip_address, machine_port)
z.disable_device()


z.enable_device()
z.disconnect()

#usuarios = usuarios['usuarios']
#for i in range(len(usuarios)):
#    user_id = usuarios[i]['usuario']
#    user_password = usuarios[i]['password']
#    admin_level = usuarios[i]['admin_level']
#    not_enabled = usuarios[i]['activado']
#    print('Usuario {}'.format(user_id))
#    print('Password {}'.format(user_password))
#    print('Admin_Level {}'.format(admin_level))
#    print('Not Enabled {}'.format(not_enabled))
#    z.set_user_info(self, user_id=user_id, name=user_id, password=user_password, card_no=0, admin_lv=admin_lv, neg_enabled=not_enabled, user_group=1)
#
#    for h in usuarios[i]['huellas']:
#        if h['huella'] != 0:
#            print(_encodeBytearray(h['huella']))
#
#

