
import psycopg2
from psycopg2.extras import DictCursor
import os
import sys
import uuid

if __name__ == '__main__':
    conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
        os.environ['ASSISTANCE_DB_HOST'],
        os.environ['ASSISTANCE_DB_USER'],
        os.environ['ASSISTANCE_DB_PASSWORD'],
        os.environ['ASSISTANCE_DB_NAME']
    ))
    cur = conn.cursor()
    try:
        host = sys.argv[1]
        db = sys.argv[2]
        user = sys.argv[3]
        passw = sys.argv[4]

        conn2 = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(host, user, passw, db))
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            cur2.execute('select distinct device_id from attlog')
            for m in cur2.fetchall():
                try:
                    cur.execute('insert into reloj (id) values (%s)',(m[0],))
                except Exception as e:
                    print(e)
                    conn.rollback()

            cur.execute('set timezone=-3')
            cur2.execute('select id, device_id, person_id, verifymode, inoutmode, date, created from attlog')
            for m in cur2.fetchall():
                cur.execute('select 1 from marcacion where id = %s', (m[0],))
                if cur.rowcount <= 0:
                    print('agregando')
                    lid = m[0]
                    dispositivo = m[1]
                    uid = m[2]
                    verificacion = m[3]
                    entrada = m[4]
                    marcacion = m[5]
                    creado = m[6]
                    cur.execute("insert into marcacion (id, creado, marcacion, tipo, dispositivo_id, usuario_id) values (%s,%s,%s,%s,%s,%s)", 
                            (lid, creado, marcacion, verificacion, dispositivo, uid))
                    conn.commit()
            

        finally:
            conn2.close()

    finally:
        conn.close()
