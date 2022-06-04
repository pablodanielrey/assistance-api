import pyzk.pyzk as pyzk
import pyzk.zkmodules.defs as defs

"""Obtiene los datos de las variables internas del dispositivo"""

ip_address = '172.25.110.29'
machine_port = 4370

z = pyzk.ZKSS()
try:
    z.connect_net(ip_address, machine_port)
    z.disable_device()

    print("ESTADISTICAS DEL EQUIPO")
    stat_keys = defs.get_status_keys()
    res = z.get_device_status(dict(zip(stat_keys, [-1]*len(stat_keys))))
    for k in res:
        print("{0} = {1}".format(k, res[k]))
    print("---------------------------------------------------")
    
    print("CONTADORES INTERNOS")
    res = z.get_device_status({'attlog_count': -1, 'user_count': -1, 'admin_count': -1})
    for k in res:
        print("{0} = {1}".format(k, res[k]))
    print("---------------------------------------------------")
    
    print("USUARIOS CON CLAVE")
    res = z.read_status(defs.STATUS['pwd_count'])
    print("{0} = {1}".format('pwd_count', res))
    print("---------------------------------------------------")
    
    print("INFORMACION DE DISPOSITIVO")
    print('Vendor = ' + z.get_vendor())
    print('Product code = |{0}|'.format(z.get_product_code()))
    print('Product time = |{0}|'.format(z.get_product_time()))
    print('card function = |{0}|'.format(z.get_cardfun()))
    print('User max id width = |{0}|'.format(z.get_device_info('~PIN2Width')))
    print('Firmware version = |{0}|'.format(z.get_firmware_version()))
    print("---------------------------------------------------")

    print("ESTADO DEL DISPOSITIVO")
    print('Device state = |{0}|'.format(z.get_device_state()))

    z.enable_device()
finally:
    z.disconnect()

