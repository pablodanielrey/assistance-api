import sys
import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
from ZKSoftware import *
logging.getLogger().setLevel(logging.INFO)

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

#El indice interno del reloj (user_sn) comienza en 1 y es secuencial
#Al insertar usuarios, previamente hay que borrar el reloj entero o bien obtener el ultimo indice actual +1 para el siguiente usuario

usuarios = usuarios['usuarios']
for i in range(len(usuarios)):
    user_sn = usuarios[i]['user_sn']
    user_id = usuarios[i]['user_id']
    user_name = usuarios[i]['user_name']
    user_password = usuarios[i]['user_password']
    card_number = usuarios[i]['card_number']
    admin_level = usuarios[i]['admin_level']
    not_enabled = usuarios[i]['not_enabled']
    user_group = usuarios[i]['user_group']
    user_tzs = usuarios[i]['user_tzs']
    
    usuario = empaquetar_usuario(user_sn,user_id,admin_level,not_enabled,user_password,
    user_name,card_number,user_group,user_tzs)
    
    subir_info_usuario(z,user_sn,usuario)

    for h in usuarios[i]['huellas']:
        if h['huella'] != 0:
            fp = encodeBytearray(h['huella'])
            fp_index = h['fp_index']
            fp_flag = h['fp_flag']
            subir_huella(z,user_sn, fp, pf_index, fp_flag)

z.enable_device()
z.disconnect()