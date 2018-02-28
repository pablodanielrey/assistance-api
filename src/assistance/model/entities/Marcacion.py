from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from model_utils import Base

class Marcacion(Base):

    __tablename__ = 'marcacion'

    marcacion = Column(DateTime)
    tipo = Column(Integer)
    usuario_id = Column(String)
    dispositivo_id = Column(String)

    reloj_id = Column(String, ForeignKey('reloj.id'))
    reloj = relationship('Reloj', back_populates='marcaciones')
