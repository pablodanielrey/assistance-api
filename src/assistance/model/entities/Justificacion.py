from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from model_utils import Base

class Justificacion(Base):

    __tablename__ = 'justificacion'

    nombre = Column(String)
    descripcion = Column(String)
    codigo = Column(String)
    general = Column(Boolean)

    justificaciones = relationship('FechaJustificada')


class FechaJustificada(Base):

    __tablename__ = 'fecha_justificada'

    fecha = Column(DateTime)

    usuario_id = Column(String, ForeignKey('usuario.id'))
    usuario = relationship('Usuario')

    justificacion_id = Column(String, ForeignKey('justificacion.id'))
    justificacion = relationship('Justificacion', back_populates='justificaciones')
