from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, with_polymorphic
import uuid

import contextlib
from .entities import Asiento, RegistroAsiento

class AsientosModel:

    def __init__(self, session, autorizador_id, notas=None):
        self.session = session
        a = Asiento(autorizador_id, notas)
        a.id = str(uuid.uuid4())
        self.asiento_id = a.id
        self.session.add(a)

    def transferencia(self, cantidad, origen, destino, descripción):
        r = RegistroAsiento()
        r.cantidad = cantidad
        r.cuenta_id = destino
        r.asiento_id = self.asiento_id
        self.session.add(r)

        r = RegistroAsiento()
        r.cantidad = - 1 * cantidad
        r.cuenta_id = origen
        r.asiento_id = self.asiento_id
        self.session.add(r)

@contextlib.contextmanager
def obtener_asiento(session, autorizador_id, notas=None):
    try:
        yield AsientosModel(session, autorizador_id, notas)
    finally:
        session.commit()


class CompensatoriosModel:

    CUENTA = '19544df3-2c33-4556-806f-07eaf0c7615b'

    def _chequear_cuentas(session):
        pass

    @staticmethod
    def _id_de_cuenta(uid):
        return '{}_{}'.format(uid, CompensatoriosModel.CUENTA)

    @classmethod
    def cambiarSaldo(cls, session, autorizador_id, uid, cantidad, notas=None):
        cuenta = CompensatoriosModel._id_de_cuenta(uid)
        with obtener_asiento(session, autorizador_id, notas) as asiento:
            asiento.transferencia(cantidad, cls.CUENTA, cuenta)

    @classmethod
    def obtenerSaldo(cls, session, uid):
        cuenta = CompensatoriosModel._id_de_cuenta(uid)
        q = session.query(RegistroAsiento).filter(RegistroAsiento.cuenta_id = cuenta).all()
        saldo = 0
        for r in q:
            saldo = saldo + r.cantidad
        return saldo