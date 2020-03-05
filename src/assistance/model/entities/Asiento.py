from sqlalchemy import Column, String, ForeignKey, Integer, Date, TIMESTAMP, DateTime
from sqlalchemy.orm import relationship
from model_utils import Base

from datetime import datetime, time, timedelta

class Asiento(Base):

    __tablename__ = 'asiento'

    fecha = Column(TIMESTAMP(timezone=True))
    notas = Column(String)
    autorizador_id = Column(String)

    def __init__(self, autorizador_id, notas=None):
        self.fecha = datetime.now()
        self.autorizador_id = autorizador_id
        self.notas = notas

class RegistroAsiento(Base):

    __tablename__ = 'registro_asiento'
    
    cantidad = Column(Integer)
    cuenta_id = Column(String)
    
    asiento_id = Column(String, ForeignKey('asiento.id'))
    asiento = relationship('Asiento')
    
