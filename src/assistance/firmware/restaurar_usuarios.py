import sys
import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
from ZKSoftware import *
logging.getLogger().setLevel(logging.INFO)

"""Restaura desde un json los usuarios y sus huellas al reloj biometrico"""

ip_address = '163.10.56.25'
machine_port = 4370

try:
    with open('/tmp/usuarios.json','r') as f:
        usuarios = json.load(f)
except Exception as e:
    print('Error: {}'.format(e))
    sys.exit(1)

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    z.read_all_user_id()
    usuarios = usuarios['usuarios']
    for i in range(len(usuarios)):
        user_id = usuarios[i]['user_id']
        user_name = usuarios[i]['user_name']
        user_password = usuarios[i]['user_password']
        card_number = usuarios[i]['card_number']
        admin_level = usuarios[i]['admin_level']
        not_enabled = usuarios[i]['not_enabled']
        user_group = usuarios[i]['user_group']
        user_tzs = usuarios[i]['user_tzs']
        z.set_user_info(user_id,name=user_name,password=user_password,
            card_no=card_number,admin_lv=admin_level, neg_enabled=not_enabled,
            user_group=user_group,user_tzs=user_tzs)

        for h in usuarios[i]['huellas']:
            fp = encodeBytearray(h['fp'])
            fp_index = h['fp_index']
            fp_flag = h['fp_flag']
            z.upload_fp(user_id=user_id,fp=fp,fp_index=fp_index,fp_flag=fp_flag)
    z.enable_device()
finally:
    z.disconnect()