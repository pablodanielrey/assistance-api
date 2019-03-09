import time
import os.path
import pyzk.pyzk as pyzk
from pyzk.zkmodules.defs import *
import logging
import json
from ZKSoftware import *
import hashlib
logging.getLogger().setLevel(logging.INFO)

try:
    with open('/tmp/usuarios.json','r') as f:
        usuarios = json.load(f)
except Exception as e:
    print('Error: {}'.format(e))
    sys.exit(1)

ip_address = '163.10.56.25'
machine_port = 4370

z = pyzk.ZKSS()
z.connect_net(ip_address, machine_port)
z.disable_device()

z.read_all_user_id()
z.read_all_fptmp()

z.enable_device()
z.disconnect()

huellasReloj = {}
for u in z.users.values():
    contador = 0
    for h,f in u.user_fptmps:
        if h != 0:
            huellasReloj[contador] = h
            contador += 1


usuarios = usuarios['usuarios']
huellasArchivo = {}
for i in range(len(usuarios)):
    contador = 0
    for h in usuarios[i]['huellas']:
        if h['huella'] != 0:
            huellasArchivo[contador] = encodeBytearray(h['huella'])
            contador += 1

md51 = hashlib.md5(huellasReloj[0]).hexdigest()
md52 = hashlib.md5(huellasArchivo[0]).hexdigest()
print('Hash 1 = {}'.format(md51))
print('Hash 2 = {}'.format(md52))
if  md51 == md52 :
    print('1 ) Son iguales')

else:
    print('1) No son iguales')

md51 = hashlib.md5(huellasReloj[1]).hexdigest()
md52 = hashlib.md5(huellasArchivo[1]).hexdigest()
print('Hash 1 = {}'.format(md51))
print('Hash 2 = {}'.format(md52))
if  md51 == md52 :
    print('2 ) Son iguales')

else:
    print('2) No son iguales')




