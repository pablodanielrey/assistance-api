import sys
import datetime
import pytz
import uuid

from users.model import open_session as open_users_session
from users.model.UsersModel import UsersModel

from assistance.model import obtener_session
from assistance.model.entities.Marcacion import Marcacion

archivo = sys.argv[1]


reloj_id = '0a609b5a-5e22-41fc-b9df-17429933ac50'

def _get_marcacion(marcacion):
    marc = datetime.datetime.strptime(marcacion,'%d/%m/%Y %H:%M:%S')
    marc += datetime.timedelta(hours=3)
    marc = pytz.utc.localize(marc)
    return marc

with open(archivo) as f:

    with obtener_session() as assis:
        with open_users_session() as users:
            for line in f:
                dni, nombres, fecha, algo, t, a = line.split(',')
                marcacion = _get_marcacion(fecha)
                print(f"DNI: {dni} - marcacion : {marcacion}")

                uid = UsersModel.get_uid_person_number(users, dni)
                print(f"dni: {dni} -- uid: {uid}")

                if assis.query(Marcacion).filter(Marcacion.marcacion == marcacion).count() > 0:
                    continue

                print(f"agregando {uid} {marcacion}")
                m = Marcacion()
                m.id = str(uuid.uuid4())
                m.dispositivo_id = reloj_id
                m.marcacion = marcacion
                m.tipo = 1
                m.usuario_id = uid
                assis.add(m)
                assis.commit()
