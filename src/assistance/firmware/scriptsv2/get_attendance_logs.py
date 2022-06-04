import logging
from zk import ZK, const

conn = None
zk = ZK('172.25.110.29', port=4370, timeout=5)
print('Connecting to device ...')
conn = zk.connect()
try:
    conn.enable_device()
    print('Firmware Version: : {}'.format(conn.get_firmware_version()))
    conn.test_voice()


    
    conn.enable_device()

except Exception as e2:
    logging.exception(e2)
    conn.disconnect()
