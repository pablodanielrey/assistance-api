import uuid
import datetime

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, with_polymorphic


import contextlib
from .entities import Asiento, RegistroAsiento

class AsientosModel:

    def __init__(self, session, autorizador_id, notas=None):
        self.session = session
        self.asiento = Asiento(autorizador_id, notas)
        self.asiento.id = str(uuid.uuid4())
        self.session.add(self.asiento)

    def transferencia(self, cantidad, origen, destino):
        r = RegistroAsiento()
        r.cantidad = cantidad
        r.cuenta_id = destino
        r.asiento_id = self.asiento.id
        self.session.add(r)

        r = RegistroAsiento()
        r.cantidad = - 1 * cantidad
        r.cuenta_id = origen
        r.asiento_id = self.asiento.id
        self.session.add(r)

@contextlib.contextmanager
def obtener_asiento(session, autorizador_id, notas=None):
    #try:
    yield AsientosModel(session, autorizador_id, notas)
    #finally:
        #session.commit()


class CompensatoriosModel:

    CUENTA = '19544df3-2c33-4556-806f-07eaf0c7615b'
    JUSTIFICACION = '48773fd7-8502-4079-8ad5-963618abe725'

    def _chequear_cuentas(session):
        pass

    @staticmethod
    def _id_de_cuenta(uid):
        return '{}_{}'.format(uid, CompensatoriosModel.CUENTA)

    @classmethod
    def cambiarSaldo(cls, session, autorizador_id, uid, cantidad, notas=None):
        cuenta = CompensatoriosModel._id_de_cuenta(uid)
        with obtener_asiento(session, autorizador_id, notas) as asientoM:
            asientoM.transferencia(cantidad, cls.CUENTA, cuenta)
            return asientoM.asiento.id

    @classmethod
    def obtenerSaldo(cls, session, uid):
        cuenta = CompensatoriosModel._id_de_cuenta(uid)
        q = session.query(RegistroAsiento).filter(RegistroAsiento.cuenta_id == cuenta).all()
        ret = {
            'saldo': 0,
            'asientos': []
        }
        for r in q:
            reg = {
                'asiento': r.asiento,
                'registros':[r]
            }
            ret['saldo'] += r.cantidad
            ret['asientos'].append(reg)
        return ret
