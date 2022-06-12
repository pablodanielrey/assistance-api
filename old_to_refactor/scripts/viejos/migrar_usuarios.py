
import psycopg2
from psycopg2.extras import DictCursor
import os

if __name__ == '__main__':
    conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
        os.environ['ASSISTANCE_DB_HOST'],
        os.environ['ASSISTANCE_DB_USER'],
        os.environ['ASSISTANCE_DB_PASSWORD'],
        os.environ['ASSISTANCE_DB_NAME']
    ))
    cur = conn.cursor()
    try:
        conn2 = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
            os.environ['OLD_ASSISTANCE_DB_HOST'],
            os.environ['OLD_ASSISTANCE_DB_USER'],
            os.environ['OLD_ASSISTANCE_DB_PASSWORD'],
            os.environ['OLD_ASSISTANCE_DB_NAME']
        ))
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            cur2.execute('select id, dni, name, lastname from profile.users where id in (select distinct user_id from assistance.attlog)')
            for m in cur2:
                cur.execute('select 1 from usuario where id = %s', (m[0],))
                if cur.rowcount <= 0:
                    cur.execute('insert into usuario (id, dni) values (%s,%s)', (m[0], m[1]))
            conn.commit()

        finally:
            conn2.close()

    finally:
        conn.close()
