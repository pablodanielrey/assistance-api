
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
            cur2.execute('select id, code, description from justifications')
            for m in cur2.fetchall():
                try:
                    t= "cur.execute('insert into justificacion (id, codigo, descripcion) values (%s,%s,%s)',(m[0],m[1],m[2]))"
                    print(t)
                    #cur.execute('insert into justificacion (id, codigo, descripcion) values (%s,%s,%s)',(m[0],m[1],m[2]))
                    conn.commit()
                except Exception as e:
                    print(e)
                    conn.rollback()

            cur2.execute('select id, justificaton_id, person_id, jstart, jend from justificationsdate where deleted = false')
            for m in cur2.fetchall():
                print('agregando')
                id = m[0]
                jid = m[1]
                uid = m[2]
                jinicio = m[3]
                jfin = m[4]
                try:
                    t= "cur.execute('insert into fecha_justificada (id, fecha_inicio, usuario_id, justificacion_id) values (%s,%s,%s,%s)',(id, jinicio, uid, jid))"
                    print(t)
                    #cur.execute("insert into fecha_justificada (id, fecha_inicio, usuario_id, justificacion_id) values (%s,%s,%s,%s)",(id, jinicio, uid, jid))
                    conn.commit()
                except Exeption as e:
                    print(e)
                    conn.rollback()
        finally:
            conn2.close()
    finally:
        conn.close()
