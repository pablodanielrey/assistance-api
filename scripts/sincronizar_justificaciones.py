
import psycopg2
from psycopg2.extras import DictCursor
import os
import logging
logging.getLogger().setLevel(logging.DEBUG)

"""
    De acuerdo al codigo en github los estados de las justificaciones son:

    UNDEFINED = 0
    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    CANCELED = 4
"""


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

        simple = [{'id':'4d7bf1d4-9e17-4b95-94ba-4ca81117a4fb', 't':'art102'},
                  {'id':'c32eb2eb-882b-4905-8e8f-c03405cee727', 't':'authority'},
                  {'id':'b309ea53-217d-4d63-add5-80c47eb76820', 't':'birthday'},
                  {'id':'e8019f0e-5a70-4ef3-922c-7c70c2ce0f8b', 't':'blood_donation'},
                  {'id':'48773fd7-8502-4079-8ad5-963618abe725', 't':'compensatory'},
                  {'id':'5289eac5-9221-4a09-932c-9f1e3d099a47', 't':'evaluation'},
                  {'id':'5c548eab-b8fc-40be-bb85-ef53d594dca9', 't':'librarian_day'},
                  {'id':'49264c80-c12a-4bc4-9ab2-0e1012f493c9', 't':'training'},
                  {'id':'3d486aa0-745a-4914-a46d-bc559853d367', 't':'weather'}]

        rango = ['family_atention',
                 'leave_without_salary',
                 'long_duration',
                 'marriage',
                 'maternity',
                 'medical_board',
                 'medical_certificate',
                 'mourning',
                 'out_ticket',
                 'paternity',
                 'pre_exam',
                 'prenatal',
                 'resolution638',
                 'short_duration',
                 'summer_break',
                 'task',
                 'travel',
                 'winter_break',
                 'informed_absence']


        count = 0
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            for jnn in simple:
                jn = jnn['t']
                logging.info(jn)
                cur2.execute('select id, user_id, owner_id, date, notes from assistance.justification_{}'.format(jn))
                for j in cur2.fetchall():
                    jid = j[0]
                    cur2.execute('select status from assistance.justification_status where justification_id = %s order by created desc limit 1', (jid,))
                    status = cur2.fetchone()
                    if status[0] == 2:
                        logging.info('obtengo')
                        logging.info(j)
                        logging.info(status)
                        logging.info(jnn['id'])

                        cur.execute('select id from fecha_justificada where id = %s', (jid,))
                        if cur.rowcount <= 0:
                            logging.info('agregando')
                            logging.info(j)
                            cur.execute('set timezone=-3; insert into fecha_justificada (id, fecha_inicio, usuario_id, responsable_id, justificacion_id) values (%s,%s,%s,%s,%s)', (jid, j[3], j[1], j[2], jnn['id']))
            conn.commit()

        finally:
            conn2.close()

    finally:
        conn.close()
