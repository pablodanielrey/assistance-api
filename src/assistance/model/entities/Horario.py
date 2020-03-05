from sqlalchemy import Column, String, ForeignKey, Integer, Date, DateTime
from sqlalchemy.orm import relationship
from model_utils import Base

from dateutil.tz import tzlocal
import pytz

from datetime import datetime, time, timedelta

class Horario(Base):

    __tablename__ = 'horario'

    fecha_valido = Column(Date)
    dia_semanal = Column(Integer)
    hora_entrada = Column(Integer)
    hora_salida = Column(Integer)
    eliminado = Column(DateTime)
    usuario_id = Column(String)

    def cantidadDeSegundos(self):
        return self.hora_salida - self.hora_entrada

    def cantidadDeMinutos(self):
        return int((self.hora_salida - self.hora_entrada) / 60)

    def esDiario(self):
        return self.hora_salida < (24 * 60 * 60)

    def obtenerHorario(self, fecha, timezone=None):
        if not timezone:
            timezone = tzlocal()
        else:
            timezone = pytz.timezone(timezone)
        dt = datetime.combine(fecha, time(0), timezone)
        # verifico que la salida sea en el mismo dia
        if self.esDiario():
            inicio = dt
            fin = dt + timedelta(hours=24)
        else:
            inicio = dt + timedelta(seconds=self.hora_entrada)
            fin = dt + timedelta(seconds=self.hora_salida)
        return (inicio, fin)

    def _localizar_fecha_en_zona(self, fecha, tz):
        timezone = pytz.timezone(tz)
        dt = datetime.combine(fecha, time(0))
        dt = timezone.localize(dt)
        return dt

    def obtenerInicioFin(self, fecha, timezone='America/Argentina/Buenos_Aires'):
        dt = self._localizar_fecha_en_zona(fecha, timezone)
        inicio = dt + timedelta(seconds=self.hora_entrada)
        fin = dt + timedelta(seconds=self.hora_salida)
        return (inicio, fin)


    def _to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def como_dict_en_zona(self, timezone):
        d = self._to_dict()
        d['fecha_valido'] = self._localizar_fecha_en_zona(self.fecha_valido, timezone)
        return d