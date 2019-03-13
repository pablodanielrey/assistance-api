from ZKSoftware import *


ip_address = '163.10.56.25'
machine_port = 4370

z = ZKSoftware(ip_address,machine_port)
print(z.obtener_marcaciones())