import sys
import os

sys.path.insert(1,os.path.abspath("./pyzk"))

from zk import ZK, const

conn = None
zk = ZK('163.10.56.126', port=4370, timeout=5)
try:
    print('Connecting to device ...')
    conn = zk.connect()
    #conn.disable_device()
    print('Firmware Version: : {}'.format(conn.get_firmware_version()))
    # print '--- Get User ---'
    users = conn.get_users()
    for user in users:
        privilege = 'User'
        if user.privilege == const.USER_ADMIN:
            privilege = 'Admin'

        print('- UID #{}'.format(user.uid))
        print('  Name       : {}'.format(user.name))
        print('  Privilege  : {}'.format(privilege))
        print('  Password   : {}'.format(user.password))
        print('  Group ID   : {}'.format(user.group_id))
        print('  User  ID   : {}'.format(user.user_id))

    print(conn.get_fp_version())

    print(conn.read_sizes())
    print(conn.fingers_cap)
    fingers = conn.get_templates()
    for f in fingers:
        print(f)


    attendances = conn.get_attendance()
    for a in attendances:
        print(a)

    conn.enable_device()
except Exception as e:
    print("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()