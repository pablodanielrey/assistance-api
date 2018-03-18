
import psycopg2
from psycopg2.extras import DictCursor
import os
import logging
logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':
    conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
        os.environ['ASSISTANCE_DB_HOST'],
        os.environ['ASSISTANCE_DB_USER'],
        os.environ['ASSISTANCE_DB_PASSWORD'],
        os.environ['ASSISTANCE_DB_NAME']
    ))
    cur = conn.cursor()
    try:
        cur.execute('select usuario_id, marcacion from marcacion')
        indice = {}
        for m in cur.fetchall():
            try:
                indice[m[0]].append(m[1])
            except KeyError as e:
                indice[m[0]] = [m[1]]

        logging.debug('indice generado')

        conn2 = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
            os.environ['OLD_ASSISTANCE_DB_HOST'],
            os.environ['OLD_ASSISTANCE_DB_USER'],
            os.environ['OLD_ASSISTANCE_DB_PASSWORD'],
            os.environ['OLD_ASSISTANCE_DB_NAME']
        ))

        count = 0
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            cur2.execute('select id, user_id, verifymode, log from assistance.attlog')
            for m in cur2.fetchall():
                count = count + 1
                if m[1] in indice and m[3] in indice[m[1]]:
                    continue
                #cur.execute('select 1 from marcacion where marcacion = %s and usuario_id = %s', (m[3],m[1]))
                #if cur.rowcount <= 0:
                cur.execute('insert into marcacion (id, usuario_id, dispositivo_id, tipo, marcacion) values (%s,%s,%s,%s,%s)', (m[0], m[1], '35fa769e-7146-4e84-a10f-f41e1e07685b', m[2], m[3]))
                logging.debug('agregando {}'.format(m))
                count = count + 1
                if count > 100:
                    count = 0
                    conn.commit()
            conn.commit()

        finally:
            conn2.close()

    finally:
        conn.close()
