from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, TIMESTAMP
from sqlalchemy.orm import relationship
from model_utils import Base

class Justificacion(Base):

    __tablename__ = 'justificacion'

    nombre = Column(String)
    descripcion = Column(String)
    codigo = Column(String)
    general = Column(Boolean)
    eliminado = Column(DateTime)

    justificaciones = relationship('FechaJustificada')


class FechaJustificada(Base):

    __tablename__ = 'fecha_justificada'

    fechaInicio = Column(TIMESTAMP(timezone=True))
    fechaFin = Column(TIMESTAMP(timezone=True))

    usuario_id = Column(String, ForeignKey('usuario.id'))
    usuario = relationship('Usuario')

    justificacion_id = Column(String, ForeignKey('justificacion.id'))
    justificacion = relationship('Justificacion', back_populates='justificaciones')
