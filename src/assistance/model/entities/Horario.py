from sqlalchemy import Column, String, ForeignKey, Integer, Date, DateTime
from sqlalchemy.orm import relationship
from model_utils import Base

class Horario(Base):

    __tablename__ = 'horario'

    fecha_valido = Column(Date)
    dia_semanal = Column(Integer)
    hora_entrada = Column(Integer)
    hora_salida = Column(Integer)
    eliminado = Column(DateTime)

    usuario_id = Column(String, ForeignKey('usuario.id'))
    usuario = relationship('Usuario')
