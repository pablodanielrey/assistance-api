import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
from ZKSoftware import *

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
z.connect_net(ip_address, machine_port)
z.disable_device()

#El indice interno del reloj (user_sn) comienza en 1 y es secuencial
#Al insertar usuarios, previamente hay que borrar el reloj entero o bien obtener el ultimo indice actual +1 para el siguiente usuario

user_sn = 6
user_id = '6'
user_name = 'uno'
user_password = '1111'
card_number = 0
admin_level = 0
not_enabled = 0
user_group = 1
user_tzs = [1,0,0]

usuario = empaquetar_usuario(user_sn,user_id,admin_level,not_enabled,user_password,
    user_name,card_number,user_group,user_tzs)

subir_info_usuario(z,user_sn,usuario)

z.enable_device()
z.disconnect()