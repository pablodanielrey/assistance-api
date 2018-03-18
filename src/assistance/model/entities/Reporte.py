from datetime import datetime, timedelta
from .Horario import Horario
from .Marcacion import Marcacion

from flask_jsontools import JsonSerializableBase

import logging
logging.getLogger().setLevel(logging.DEBUG)

class RenglonReporte:
    '''
    fecha: Date;
    horario: Horario;
    marcaciones: Marcacion[];
    entrada: Marcacion;
    salida: Marcacion;
    cantidad_horas_trabajadas: number;
    justifcacion: FechaJustificada;
    '''
    def __init__(self, fecha, horario, marcaciones, justificacion):
        self.fecha = fecha
        self.horario = horario
        self.marcaciones = marcaciones
        self.entrada = marcaciones[0] if len(marcaciones) > 0 else None
        self.salida = marcaciones[-1] if len(marcaciones) > 0 else None
        self.justificacion = justificacion
        self.cantidad_horas_trabajadas = self.calcularHorasTrabajadas()

    def calcularHorasTrabajadas(self):
        seconds = 0
        for k in range(0, len(self.marcaciones), 2):
            try:
                e = self.marcaciones[k].marcacion
                s = self.marcaciones[ k + 1].marcacion
                seconds = seconds + (s - e).seconds
            except IndexError as e:
                continue
        return seconds

    def __json__(self):
        return self.__dict__

class Reporte:

    '''
    usuario: Usuario;
    fecha_inicial: Date;
    fecha_final: Date;
    reportes: RenglonReporte[] = [];
    detalle: Detalle;
    '''

    def __init__(self, u, inicio, fin):
        self.usuario = u
        self.fecha_inicial = inicio
        self.fecha_final = fin
        self.reportes = []
        self.detalle = None


    @classmethod
    def _agregar_marcaciones_sin_horario(cls, session, reportes, uid, inicio, fin):
        ''' obtengo las marcaciones que faltan '''
        ids_marcaciones_registradas = []
        for r in reportes:
            ids_marcaciones_registradas.extend([m.id for m in r.marcaciones])
        sin_horario = session.query(Marcacion).filter(Marcacion.usuario_id == uid, Marcacion.marcacion >= inicio, Marcacion.marcacion <= fin, ~Marcacion.id.in_(ids_marcaciones_registradas)).all()
        sin_horario = sorted(sin_horario, key=lambda x: x.marcacion)

        ''' las agrupo por fecha '''
        por_fecha = {}
        for m in sin_horario:
            if m.marcacion.date() in por_fecha:
                por_fecha[m.marcacion.date()].append(m)
            else:
                por_fecha[m.marcacion.date()] = [m]

        ''' elimino los RenglonReporte a ser reemplazados '''
        reportes_filtrados = [r for r in reportes if r.fecha not in por_fecha]
        for k in por_fecha:
            r = RenglonReporte(k, None, por_fecha[k], None)
            reportes_filtrados.append(r)
        return sorted(reportes_filtrados, key=lambda x: x.fecha)


    @classmethod
    def generarReporte(cls, session, usuario, inicio, fin):
        if inicio > fin:
            return []

        reportes = []
        for i in range(0, int((fin - inicio).days + 1)):
            actual = inicio + timedelta(days=i)

            q = session.query(Horario)
            q = q.filter(Horario.usuario_id == usuario['id'], Horario.dia_semanal == actual.weekday(), Horario.fecha_valido <= actual)
            q = q.order_by(Horario.fecha_valido.desc())
            horario = q.limit(1).one_or_none()

            marcaciones = Marcacion.obtenerMarcaciones(session, horario, usuario['id'], actual)
            marcaciones = [] if marcaciones is None else marcaciones
            justificacion = None
            r = RenglonReporte(actual, horario, marcaciones, justificacion)
            reportes.append(r)

        rep = Reporte(usuario, inicio, fin)
        rep.reportes = cls._agregar_marcaciones_sin_horario(session, reportes, usuario['id'], inicio, fin)
        return rep

    def __json__(self):
        return self.__dict__


class Detalle:

    def __init__(self):
        self.justifiaciones = None

    def __json__(self):
        return self.__dict__
