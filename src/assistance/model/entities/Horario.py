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

    def obtenerInicioFin(self, fecha, timezone=None):
        if not timezone:
            timezone = tzlocal()
            print ('Timezone Local establecida ---->',  timezone)
        else:
            print ('Timezone Enviada por parametro sin procesar ---->',  timezone)
            timezone = pytz.timezone(timezone)
            print ('Timezone Enviada por parametro procesada ---->',  timezone)
        dt = datetime.combine(fecha, time(0), timezone)
        inicio = dt + timedelta(seconds=self.hora_entrada)
        fin = dt + timedelta(seconds=self.hora_salida)
        return (inicio, fin)
