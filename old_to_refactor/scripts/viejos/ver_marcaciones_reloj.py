
import logging
import os
from assistance.model.zkSoftware import ZkSoftware

if __name__ == '__main__':

    ip = os.environ['ip']
    puerto = os.environ['puerto']
    zona_horaria = 'America/Argentina/Buenos_Aires'

    zk = ZkSoftware(host=reloj.ip, port=reloj.puerto, timezone=zona_horaria)
    logs = zk.getAttLog()
    logging.info(logs)
