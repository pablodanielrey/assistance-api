import logging
from time import sleep
from zk import ZK, const

conn = None
zk = ZK('172.25.110.29', port=4370, timeout=5)
print('Connecting to device ...')
conn = zk.connect()
try:
    print('Disabling device ...')
    conn.disable_device()
    print('Firmware Version: : {}'.format(conn.get_firmware_version()))
    # for voice in range(0,55):
    #     print(f"haciendo sonar : {voice}")
    #     conn.test_voice(index=voice)
    #     sleep(2)

    # conn.test_voice(index=10)
    # conn.test_voice(index=11)
    # conn.test_voice(index=13)
    conn.test_voice(index=51)

    conn.enable_device()
except Exception as e2:
    logging.exception(e2)
    conn.disconnect()
