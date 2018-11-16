import contextlib
import datetime

from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, TIMESTAMP, desc
from sqlalchemy.orm import relationship
from model_utils import Base



class Asiento(Base):

    __tablename__ = 'asiento'

    fecha = Column(TIMESTAMP(timezone=True))
    notas = Column(String)
    autorizador_id = Column(String)

    def __init__(self, autorizador_id, notas=None):
        self.fecha = datetime.datetime.now()
        self.autorizador_id = autorizador_id
        self.notas = notas

class Cuenta(Base):

    __tablename__ = 'cuenta_asiento'

    nombre = Column(String)
    descripcion = Column(String)
    usuario_id = Column(String)


class RegistroAsiento(Base):

     __tablename__ = 'registro_asiento'

    cantidad = Column(Integer)
    cuenta_id = Column(String, ForeignKey('cuenta_asiento.id'))
    asiento_id = Column(String, ForeignKey('asiento.id'))
    

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
        r.cantidad = -1 * cantidad
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

    def _chequear_cuentas(session):
        pass