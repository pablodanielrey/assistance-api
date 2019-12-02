from ZKSoftware import *


ip_address = '163.10.56.25'
machine_port = 4370

z = ZKSoftware(ip_address,machine_port)
z.connect()
try:
    z.disable_device()
    try:
        marcaciones = z.obtener_marcaciones()
        print(marcaciones)
        #z.borrar_marcaciones()
    finally:
        z.enable_device()
finally:
    z.disconnect()

#marcaciones = z.obtener_marcaciones()
#z.borrar_marcaciones()
#print(marcaciones)