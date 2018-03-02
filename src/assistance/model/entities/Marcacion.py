from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from model_utils import Base

from datetime import datetime, timedelta

class Marcacion(Base):

    TOLERANCIA_DUPLICADA = 5                # en minutos
    TOLERANCIA_DIARIA = 60                  # en minutos

    __tablename__ = 'marcacion'

    marcacion = Column(TIMESTAMP(timezone=True))
    tipo = Column(Integer)
    usuario_id = Column(String)

    dispositivo_id = Column(String, ForeignKey('reloj.id'))
    dispositivo = relationship('Reloj')

    usuario_id = Column(String, ForeignKey('usuario.id'))
    usuario = relationship('Usuario')


    @classmethod
    def obtenerMarcaciones(cls, session, horario, uid, actual):
        if horario is None:
            return None

        inicio, fin = horario.obtenerHorario(actual)

        tolerancia = timedelta(minutes=cls.TOLERANCIA_DUPLICADA)
        toleranciaDiaria = timedelta() if horario.esDiario() else timedelta(minutes=cls.TOLERANCIA_DIARIA)

        tinicio, tfin = inicio - toleranciaDiaria, fin + toleranciaDiaria

        ls = []

        ''' agrupo por tolerancia duplicada los logs '''
        marcaciones = session.query(Marcacion).filter(Marcacion.usuario_id == uid, Marcacion.marcacion >= tinicio, Marcacion.marcacion <= tfin).all()
        for m in marcaciones:
            try:
                ultimo = ls[-1]
                ultimo = ultimo.marcacion + tolerancia
                if m.marcacion <= ultimo:
                    continue
                ls.append(m)
            except IndexError as e:
                ls.append(m)
