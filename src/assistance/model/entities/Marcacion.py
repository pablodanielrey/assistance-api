from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from model_utils import Base

class Marcacion(Base):

    marcacion = Column(DateTime)
    tipo = Column(Integer)

    reloj_id = Column(String, ForeignKey('reloj.id'))
    reloj = relationship('Reloj')
