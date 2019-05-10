import psycopg2
from psycopg2.extras import DictCursor
import os
import sys
import logging
import datetime

from assistance.model import obtener_session
from assistance.model.AsientosModel import CompensatoriosModel

"""Script de migracion de Compensatorios"""
"""Inserta compensatorios existentes del sistema anterior al nuevo sistema"""

OLD_ASSISTANCE_DB_HOST = os.environ['OLD_ASSISTANCE_DB_HOST']
OLD_ASSISTANCE_DB_USER = os.environ['OLD_ASSISTANCE_DB_USER']
OLD_ASSISTANCE_DB_PASSWORD = os.environ['OLD_ASSISTANCE_DB_PASSWORD']
OLD_ASSISTANCE_DB_NAME = os.environ['OLD_ASSISTANCE_DB_NAME']

CUENTA = '19544df3-2c33-4556-806f-07eaf0c7615b'
JUSTIFICACION = '48773fd7-8502-4079-8ad5-963618abe725'

ID_DE_AUTORIZADOR = '1'

def _id_de_cuenta(uid):
    return '{}_{}'.format(uid, CUENTA)

if __name__ == '__main__':
    try:
        conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
            OLD_ASSISTANCE_DB_HOST, OLD_ASSISTANCE_DB_USER, OLD_ASSISTANCE_DB_PASSWORD, OLD_ASSISTANCE_DB_NAME
        ))
        cur = conn.cursor()
        cur.execute('select user_id, stock, updated from assistance.justification_compensatory_stock where stock > 0')
        cartera = {}
        for c in cur.fetchall():
            cartera[c[0]] = {
                'id':c[0],
                'stock': c[1],
                'fecha': c[2]
            }

    finally:
        conn.close()

    for u in cartera:
        logging.info('Usuario: {} - Compensatorios: {}'.format(u,cartera[u]))
    logging.info('Encontrados: {}'.format(len(cartera)))

    """
        Si la fecha de actualización es mayor a la fecha de los asientos entocnes se generan.
        si no, no se suma nada.
        la relacion de las entidades es:

        Asiento {
            fecha
            notas
            autorizador_id
            registros = [
                {
                    cantidad,
                    cuenta_id
                }
            ]
        }
    """
    with obtener_session() as session:
        for u in cartera:
            logging.info('procesando : {}'.format(u['id']))
            saldo = CompensatoriosModel.obtenerSaldo(session, u['id'])
            fecha = datetime.datetime.now()
            reg_a_aplicar = None
            for asiento in saldo['asientos']:
                if asiento.fecha > fecha:
                    fecha = asiento.fecha
                    reg_a_aplicar = saldo

            if reg_a_aplicar:
                saldo_a_aplicar = u['stock'] - reg_a_aplicar['saldo']
                if saldo_a_aplicar > 0:
                    CompensatoriosModel.cambiarSaldo(session, ID_DE_AUTORIZADOR, saldo_a_aplicar, notas='Importación del stock del sistema anterior')

        #session.commit()
            

    
