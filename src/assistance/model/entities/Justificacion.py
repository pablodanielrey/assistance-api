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

    fecha_inicio = Column(TIMESTAMP(timezone=True))
    fecha_fin = Column(TIMESTAMP(timezone=True))

    eliminado = Column(DateTime)

    usuario_id = Column(String)
    autorizador_id = Column(String)

    justificacion_id = Column(String, ForeignKey('justificacion.id'))
    justificacion = relationship('Justificacion', back_populates='justificaciones')
