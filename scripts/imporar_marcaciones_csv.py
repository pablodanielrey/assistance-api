import sys
import datetime
import pytz

from users.model import open_session as open_users_session
from users.model.UsersModel import UsersModel

from assistance.model import obtener_session
from assistance.model.entities.Marcacion import Marcacion

archivo = sys.argv[1]


def _get_marcacion(marcacion):
    marc = datetime.datetime.strptime(marcacion,'%d/%m/%Y %H:%M:%S')
    marc += datetime.timedelta(hours=3)
    marc = pytz.utc.localize(marc)
    return marc

with open(archivo) as f:
    for line in f:
        dni, nombres, fecha, algo, t, a = line.split(',')
        marcacion = _get_marcacion(fecha)
        print(f"DNI: {dni} - marcacion : {marcacion}")

        with open_session() as session:
            uid = UsersModel.get_uid_person_number(session, dni)
            print(f"dni: {dni} -- uid: {uid}")


