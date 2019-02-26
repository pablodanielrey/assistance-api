
import psycopg2
from psycopg2.extras import DictCursor
import os
import logging
logging.getLogger().setLevel(logging.DEBUG)
import uuid
import datetime

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

        rango = [{'id':'b80c8c0e-5311-4ad1-94a7-8d294888d770', 't':'family_atention'},
                 {'id':'1c14a13c-2358-424f-89d3-d639a9404579', 't':'leave_without_salary'},
                 {'id':'a93d3af3-4079-4e93-a891-91d5d3145155', 't':'long_duration'},
                 {'id':'30a249d5-f90c-4666-aec6-34c53b62a447', 't':'marriage'},
                 {'id':'68bf4c98-984d-4b71-98b0-4165c69d62ce', 't':'maternity'},
                 {'id':'90b3b99a-fcf7-48b1-845f-764ee58eb427', 't':'medical_board'},
                 {'id':'478a2e35-51b8-427a-986e-591a9ee449d8', 't':'medical_certificate'},
                 {'id':'0cd276aa-6d6b-4752-abe5-9258dbfd6f09', 't':'mourning'},
                 {'id':'fa64fdbd-31b0-42ab-af83-818b3cbecf46', 't':'out_ticket'},
                 {'id':'4939cd4d-29d7-487c-af01-7aaecc4b76d0', 't':'paternity'},
                 {'id':'b70013e3-389a-46d4-8b98-8e4ab75335d0', 't':'pre_exam'},
                 {'id':'aa41a39e-c20e-4cc4-942c-febe95569499', 't':'prenatal'},
                 {'id':'50998530-10dd-4d68-8b4a-a4b7a87f3972', 't':'resolution638'},
                 {'id':'f9baed8a-a803-4d7f-943e-35c436d5db46', 't':'short_duration'},
                 {'id':'76bc064a-e8bf-4aa3-9f51-a3c4483a729a', 't':'summer_break'},
                 {'id':'cb2b4583-2f44-4db0-808c-4e36ee059efe', 't':'task'},
                 {'id':'7747e3ff-bbe2-4f2e-88f7-9cc624a242a9', 't':'travel'},
                 {'id':'f7464e86-8b9e-4415-b370-b44b624951ca', 't':'winter_break'}]

        jdate = [{'id':'e0dfcef6-98bb-4624-ae6c-960657a9a741', 't':'informed_absence'}]

        usuarios_comparados = set()

        count = 0
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            for jnn in simple:
                jn = jnn['t']
                logging.info(jn)
                cur2.execute('select id, user_id, owner_id, date, notes from assistance.justification_{} order by date'.format(jn))
                for j in cur2.fetchall():
                    jid = j[0]
                    cur2.execute('select status from assistance.justification_status where justification_id = %s order by created desc limit 1', (jid,))
                    status = cur2.fetchone()
                    if status[0] == 1:
                        logging.info('obtengo')
                        logging.info(j)
                        logging.info(status)
                        logging.info(jnn['id'])

                        tjid = str(uuid.uuid4())
                        tfecha = datetime.datetime.now()
                        cur2.execute('insert into assistance.justification_status (id,status,user_id,justification_id,created,date) values (%s,%s,%s,%s,%s)', (tjid, 2, '1', jid, tfecha, tfecha))
                        cur2.commit()

            for jnn in jdate:
                jn = jnn['t']
                logging.info(jn)
                cur2.execute('select id, user_id, owner_id, jdate, notes from assistance.justification_{} order by jdate'.format(jn))
                for j in cur2.fetchall():
                    jid = j[0]
                    cur2.execute('select status from assistance.justification_status where justification_id = %s order by created desc limit 1', (jid,))
                    status = cur2.fetchone()
                    if status[0] == 1:
                        logging.info('obtengo')
                        logging.info(j)
                        logging.info(status)
                        logging.info(jnn['id'])

                        tjid = str(uuid.uuid4())
                        tfecha = datetime.datetime.now()
                        cur2.execute('insert into assistance.justification_status (id,status,user_id,justification_id,created,date) values (%s,%s,%s,%s,%s)', (tjid, 2, '1', jid, tfecha, tfecha))
                        cur2.commit()

            for jnn in rango:
                jn = jnn['t']
                logging.info(jn)
                cur2.execute('select id, user_id, owner_id, jstart, jend, notes from assistance.justification_{} order by jstart'.format(jn))
                for j in cur2.fetchall():
                    jid = j[0]
                    cur2.execute('select status from assistance.justification_status where justification_id = %s order by created desc limit 1', (jid,))
                    status = cur2.fetchone()
                    if status[0] == 1:
                        logging.info('obtengo')
                        logging.info(j)
                        logging.info(status)
                        logging.info(jnn['id'])

                        tjid = str(uuid.uuid4())
                        tfecha = datetime.datetime.now()
                        cur2.execute('insert into assistance.justification_status (id,status,user_id,justification_id,created,date) values (%s,%s,%s,%s,%s)', (tjid, 2, '1', jid, tfecha, tfecha))
                        cur2.commit()


        finally:
            conn2.close()

    finally:
        conn.close()
