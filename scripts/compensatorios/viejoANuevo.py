import psycopg2
from psycopg2.extras import DictCursor
import os
import sys

"""Script de migracion de Compensatorios"""
"""Inserta compensatorios existentes del sistema anterior al nuevo sistema"""

OLD_ASSISTANCE_DB_HOST = os.environ['OLD_ASSISTANCE_DB_HOST']
OLD_ASSISTANCE_DB_USER = os.environ['OLD_ASSISTANCE_DB_USER']
OLD_ASSISTANCE_DB_PASSWORD = os.environ['OLD_ASSISTANCE_DB_PASSWORD']
OLD_ASSISTANCE_DB_NAME = os.environ['OLD_ASSISTANCE_DB_NAME']

CUENTA = '19544df3-2c33-4556-806f-07eaf0c7615b'
JUSTIFICACION = '48773fd7-8502-4079-8ad5-963618abe725'

def _id_de_cuenta(uid):
    return '{}_{}'.format(uid, CUENTA)

if __name__ == '__main__':
    try:
        conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
            OLD_ASSISTANCE_DB_HOST, OLD_ASSISTANCE_DB_USER, OLD_ASSISTANCE_DB_PASSWORD, OLD_ASSISTANCE_DB_NAME
        ))
        cur = conn.cursor()
        cur.execute('select user_id, stock from assistance.justification_compensatory_stock where stock > 0')
        cartera = {}
        for c in cur.fetchall():
            cartera[c[0]] = c[1]

    finally:
        conn.close()

    for u in cartera:
        print('Usuario: {} - Compensatorios: {}'.format(u,cartera[u]))
    print('Encontrados: {}'.format(len(cartera)))
    
