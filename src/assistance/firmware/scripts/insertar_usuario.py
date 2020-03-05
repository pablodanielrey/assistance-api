import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
from ZKSoftware import *

"""Codigo de prueba utilizando libreria, inserta usuario desde variables"""

ip_address = '163.10.56.25'
machine_port = 4370

user_id = '11223345'
user_name = 'Prueba'
user_password = ''
card_number = 0
admin_level = 0
not_enabled = 0
user_group = 1
user_tzs = [1,0,0]

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    z.read_all_user_id()
    z.set_user_info(user_id,name=user_name,password=user_password,
        card_no=card_number,admin_lv=admin_level, neg_enabled=not_enabled,
        user_group=user_group,user_tzs=user_tzs)
    z.enable_device()
finally:
    z.disconnect()

#El indice interno del reloj (user_sn) comienza en 1 y es secuencial
#Al insertar usuarios, previamente hay que borrar el reloj entero o bien obtener el ultimo indice actual +1 para el siguiente usuario

#usuario = empaquetar_usuario(user_sn,user_id,admin_level,not_enabled,user_password,
#    user_name,card_number,user_group,user_tzs)
#
#subir_info_usuario(z,user_sn,usuario)


#if z.id_exists(user_id):
#    print('El usuario ya existe. Actualizando Datos.')
#    user_sn = z.id_to_sn(user_id)
#    z.set_user_info()
#    z.users[user_sn].user_name = user_name
#    z.users[user_sn].user_password = user_password
#    z.users[user_sn].card_number = card_number
#    z.users[user_sn].admin_level = admin_level
#    z.users[user_sn].not_enabled = not_enabled
#    z.users[user_sn].user_group =  user_group
#    z.users[user_sn].user_tzs = user_tzs
#    z.upload_user_info(user_id)
#    
#else:
#    print('Agregando Usuario.')
#    user_sn = z.create_user()
#    z.users[user_sn].user_id = user_id
#    z.users[user_sn].user_name = user_name
#    z.users[user_sn].user_password = user_password
#    z.users[user_sn].card_number = card_number
#    z.users[user_sn].admin_level = admin_level
#    z.users[user_sn].not_enabled = not_enabled
#    z.users[user_sn].user_group =  user_group
#    z.users[user_sn].user_tzs = user_tzs
#    z.upload_user_info(user_id)