import psycopg2
from psycopg2.extras import DictCursor
import os
import sys

"""Script de Sincronizacion de Compensatorios"""
"""Inserta compensatorios creados en el nuevo sistema al viejo"""

CUENTA = '19544df3-2c33-4556-806f-07eaf0c7615b'

def _id_de_cuenta(uid):
    return '{}_{}'.format(uid, CUENTA)

if __name__ == '__main__':
    try:
        conn = psycopg2.connect("host='{}' user='{}' password='{}' port='{}' dbname={}".format(
            os.environ['ASSISTANCE_DB_HOST'],
            os.environ['ASSISTANCE_DB_USER'],
            os.environ['ASSISTANCE_DB_PASSWORD'],
            os.environ['ASSISTANCE_DB_PORT'],
            os.environ['ASSISTANCE_DB_NAME']
        ))
        cur = conn.cursor()
        cur.execute('select cantidad, cuenta_id from registro_asiento where cuenta_id != %s',(CUENTA,))
        cartera = {}
        for c in cur.fetchall():
            uid = c[1].split('_')[0]
            if uid in cartera:
                cartera[uid] += c[0]
            else:
                cartera[uid] = c[0]
            print('Cuenta: {} Cantidad: {}'.format(uid,c[0]))

    finally:
        conn.close()
    
