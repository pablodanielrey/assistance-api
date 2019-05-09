from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, TIMESTAMP, desc
from sqlalchemy.orm import relationship
from model_utils import Base
import logging
logging.getLogger().setLevel(logging.DEBUG)

import pytz
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

    def obtenerFechaRelativa(self, tz='America/Argentina/Buenos_Aires'):
        timezone = pytz.timezone(tz)
        return self.marcacion.astimezone(timezone).date()

    def obtenerFechaHoraRelativa(self, tz='America/Argentina/Buenos_Aires'):
        timezone = pytz.timezone(tz)
        return self.marcacion.astimezone(timezone)

    def esIgual(self, otra=None, tolerancia=None):
        ''' tiene en cuenta la tolerancia para decidir si representan la misma marcacion '''
        if not otra:
            return False
        if not tolerancia:
            return self.marcacion == otra.marcacion
        if self.marcacion > otra.marcacion:
            return otra.marcacion + tolerancia >= self.marcacion
        else:
            return self.marcacion + tolerancia >= otra.marcacion


    @classmethod
    def obtenerMarcaciones(cls, session, horario, uid, fecha, tz='America/Argentina/Buenos_Aires'):
        if horario is None:
            return None, []

        inicio, fin = horario.obtenerHorario(fecha,timezone=tz)

        tolerancia = timedelta(minutes=cls.TOLERANCIA_DUPLICADA)
        toleranciaDiaria = timedelta() if horario.esDiario() else timedelta(minutes=cls.TOLERANCIA_DIARIA)

        tinicio, tfin = inicio - toleranciaDiaria, fin + toleranciaDiaria

        ls = []
        duplicadas = []

        ''' agrupo por tolerancia duplicada los logs '''
        marcaciones = session.query(Marcacion).filter(Marcacion.usuario_id == uid, Marcacion.marcacion >= tinicio, Marcacion.marcacion <= tfin).order_by(Marcacion.marcacion).all()
        for m in marcaciones:
            try:
                ultimo = ls[-1]
                if ultimo.esIgual(m,tolerancia):
                    duplicadas.append(m)
                    continue
                ls.append(m)
            except IndexError as e:
                ls.append(m)
        return ls, duplicadas
