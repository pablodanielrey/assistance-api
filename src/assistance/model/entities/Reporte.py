from datetime import datetime, time, timedelta
import pytz
from .Horario import Horario
from .Marcacion import Marcacion

from flask_jsontools import JsonSerializableBase

import logging
logging.getLogger().setLevel(logging.DEBUG)

class Detalle:

    def __init__(self):
        self.justificaciones = {}
        self.dias_seleccionados = 0

        self.dias_laborables = 0
        self.dias_trabajados = 0
        self.faltas_justificadas = 0
        self.faltas_injustificadas = 0

        self.minutos_laborables = 0
        self.minutos_trabajados = 0
        self.minutos_justificados = 0
        self.minutos_injustificados = 0

        self.minutos_minimos_hora_extra_no_lab = 0
        self.minutos_bloque_hora_extra_no_lab = 0
        self.minutos_minimos_hora_extra_lab = 0
        self.minutos_bloque_hora_extra_lab = 0

        self.minutos_extra_en_dias_laborables = 0
        self.minutos_extra_descartados_en_dias_laborables = 0
        self.dias_extra_trabajados = 0
        self.minutos_extra_descartados = 0
        self.minutos_extra = 0
        self.minutos_extra_totales = 0
        self.minutos_extra_descartados_totales = 0

        self.dias_totales_trabajados = 0
        self.minutos_totales_trabajados = 0

        self.salidas_tempranas = 0
        self.salidas_tardes = 0
        self.minutos_salidas_tempranas = 0
        self.minutos_salidas_tardes = 0

        self.entradas_tempranas = 0
        self.entradas_tardes = 0
        self.minutos_entradas_tempranas = 0
        self.minutos_entradas_tardes = 0

    def _calcularMinutosExtra(self, minutos_trabajados, minutos_a_trabajar, minutos_minimos_para_hora_extra, bloque_de_minutos_para_hora_extra):
        me = minutos_trabajados - minutos_a_trabajar
        if me <= 0:
            return 0, 0
        minutos_extra_descartados = 0
        minutos_extra = 0
        if me < minutos_minimos_para_hora_extra:
            minutos_extra_descartados = me
        else:
            if bloque_de_minutos_para_hora_extra:
                cantidad_bloques = int(me / bloque_de_minutos_para_hora_extra)
                minutos_extra = cantidad_bloques * bloque_de_minutos_para_hora_extra
                minutos_extra_descartados = (me % bloque_de_minutos_para_hora_extra)
            else:
                minutos_extra = me

        return minutos_extra, minutos_extra_descartados

    def calcular(self, reporte, minutos_minimos_para_hora_extra=30, bloque_de_minutos_para_hora_extra=30):
        '''
            minutos_minimos_para_hora_extra == los minutos necesarios minimos adicionales -- si es 0 entnoces cada minuto extra ya contabiliza
            bloque_de_minutos_para_hora_extra == minutos necesarios para contabilizar para hora extra -- si es None cada minuto cuenta para hora extra.
        '''

        self.dias_seleccionados = int((reporte.fecha_final - reporte.fecha_inicial).days) + 1
        self.minutos_minimos_hora_extra_no_lab = 0
        self.minutos_bloque_hora_extra_no_lab = 0
        self.minutos_minimos_hora_extra_lab = minutos_minimos_para_hora_extra
        self.minutos_bloque_hora_extra_lab = bloque_de_minutos_para_hora_extra



        for renglon in reporte.reportes:
            minutos_trabajados = renglon.cantidad_segundos_trabajados / 60
            minutos_a_trabajar = 0

            if renglon.horario:
                minutos_a_trabajar = renglon.horario.cantidadDeMinutos()

                ''' dias laborables TODO: falta analizar el tema de las justificaciones generales a ver si descuenta '''
                self.dias_laborables = self.dias_laborables + 1
                if minutos_a_trabajar > 0:
                    self.minutos_laborables = self.minutos_laborables + minutos_a_trabajar

                ''' dias trabajados '''
                if renglon.entrada or minutos_trabajados > 0:
                    self.dias_trabajados = self.dias_trabajados + 1
                    if minutos_trabajados <= minutos_a_trabajar:
                        self.minutos_trabajados = self.minutos_trabajados + minutos_trabajados
                    else:
                        self.minutos_trabajados = self.minutos_trabajados + minutos_a_trabajar
                        minutos_extra, extra_descartados = self._calcularMinutosExtra(minutos_trabajados, minutos_a_trabajar, self.minutos_minimos_hora_extra_lab, self.minutos_bloque_hora_extra_lab)
                        self.minutos_extra_en_dias_laborables = self.minutos_extra_en_dias_laborables + minutos_extra
                        self.minutos_extra_descartados_en_dias_laborables = self.minutos_extra_descartados_en_dias_laborables + extra_descartados

                ''' calculo los minutos sin trabajar '''
                if minutos_a_trabajar > 0 and minutos_trabajados < minutos_a_trabajar:
                    if renglon.justificacion:
                        self.minutos_justificados = self.minutos_justificados + (minutos_a_trabajar - minutos_trabajados)
                    else:
                        self.minutos_injustificados = self.minutos_injustificados + (minutos_a_trabajar - minutos_trabajados)

                ''' calculo las faltas '''
                if minutos_a_trabajar > 0 and not renglon.entrada:
                    if renglon.justificacion:
                        self.faltas_justificadas = self.faltas_justificadas + 1
                    else:
                        self.faltas_injustificadas = self.faltas_injustificadas + 1


                inicio, fin = renglon.horario.obtenerInicioFin(renglon.fecha)

                ''' salidas '''
                salida = renglon.salida.marcacion if renglon.salida else None
                if salida and salida < fin:
                    self.salidas_tempranas = self.salidas_tempranas + 1
                    self.minutos_salidas_tempranas = self.minutos_salidas_tempranas + int((fin - salida).seconds / 60)
                if salida and salida > fin:
                    self.salidas_tardes = self.salidas_tardes + 1
                    self.minutos_salidas_tardes = self.minutos_salidas_tardes + int((salida - fin).seconds / 60)

                ''' entradas '''
                entrada = renglon.entrada.marcacion if renglon.entrada else None
                if entrada and entrada < inicio:
                    self.entradas_tempranas = self.entradas_tempranas + 1
                    self.minutos_entradas_tempranas = self.minutos_entradas_tempranas + int((inicio - entrada).seconds / 60)
                if entrada and entrada > inicio:
                    self.entradas_tardes = self.entradas_tardes + 1
                    self.minutos_entradas_tardes = self.minutos_entradas_tardes + int((entrada - inicio).seconds / 60)


            else:
                ''' calculo horas extras '''
                minutos_extra, extra_descartados = self._calcularMinutosExtra(minutos_trabajados, minutos_a_trabajar, self.minutos_minimos_hora_extra_no_lab, self.minutos_bloque_hora_extra_no_lab)
                self.minutos_extra = self.minutos_extra + minutos_extra
                self.minutos_extra_descartados = self.minutos_extra_descartados + extra_descartados
                if minutos_extra > 0 or extra_descartados > 0:
                    self.dias_extra_trabajados = self.dias_extra_trabajados + 1


            ''' calculo las justificaciones '''
            if renglon.justificacion:
                k = renglon.justificacion.nombre
                try:
                    self.justificaciones[k] = self.justificaciones[k] + 1
                except KeyError as e:
                    self.justificaciones[k] = 1



        self.dias_totales_trabajados = self.dias_trabajados + self.dias_extra_trabajados
        self.minutos_totales_trabajados = self.minutos_trabajados + self.minutos_extra + self.minutos_extra_descartados + self.minutos_extra_en_dias_laborables + self.minutos_extra_descartados_en_dias_laborables
        self.minutos_extra_totales = self.minutos_extra + self.minutos_extra_en_dias_laborables
        self.minutos_extra_descartados_totales = self.minutos_extra_descartados + self.minutos_extra_descartados_en_dias_laborables


    def __json__(self):
        return self.__dict__


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
    def __init__(self, fecha, horario, marcaciones, duplicadas, justificacion):
        self.fecha = fecha
        self.horario = horario
        self.marcaciones = marcaciones
        self.duplicadas = duplicadas
        self.entrada = marcaciones[0] if len(marcaciones) > 0 else None
        self.salida = marcaciones[-1] if len(marcaciones) > 0 and len(marcaciones) % 2 == 0 else None
        self.justificacion = justificacion
        self.cantidad_segundos_trabajados = self._calcularSegundosTrabajados()
        self.cantidad_horas_trabajadas = self.cantidad_segundos_trabajados

    def _calcularSegundosTrabajados(self):
        seconds = 0
        for k in range(0, len(self.marcaciones), 2):
            try:
                e = self.marcaciones[k].marcacion
                s = self.marcaciones[k + 1].marcacion
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
    def _agregar_marcaciones_sin_horario(cls, session, reportes, uid, inicio, fin, tzone='America/Argentina/Buenos_Aires'):
        """
            Las marcaciones sin horario se toman como diarias. o sea dentro del mismo día de marcado.
            hay que tener en cuenta que cuando se saca el date() debe ser relativo a la zona horaria del cliente
            se supone America/Argentina/Buenos_Aires
        """
        timezone = pytz.timezone(tzone)
        inicio = datetime.combine(inicio,time(0)).replace(tzinfo=timezone)
        fin = datetime.combine(fin,time(0)).replace(tzinfo=timezone) + timedelta(days=1)

        ''' obtengo las marcaciones que faltan '''
        ids_marcaciones_registradas = []
        for r in reportes:
            ids_marcaciones_registradas.extend([m.id for m in r.marcaciones])
            ids_marcaciones_registradas.extend([m.id for m in r.duplicadas])
        sin_horario = session.query(Marcacion).filter(Marcacion.usuario_id == uid, Marcacion.marcacion >= inicio, Marcacion.marcacion <= fin, ~Marcacion.id.in_(ids_marcaciones_registradas)).all()
        if len(sin_horario) <= 0:
            return reportes
        sin_horario = sorted(sin_horario, key=lambda x: x.marcacion)

        ''' las agrupo por fecha '''
        tolerancia = timedelta(minutes=Marcacion.TOLERANCIA_DUPLICADA)
        por_fecha = {}
        for m in sin_horario:
            fecha = m.obtenerFechaRelativa(tzone)
            if fecha in por_fecha:
                ''' tengo en cuenta la tolerancia '''
                if not por_fecha[fecha][-1].esIgual(m,tolerancia):
                    por_fecha[fecha].append(m)
            else:
                por_fecha[fecha] = [m]

        ''' elimino los RenglonReporte a ser reemplazados '''
        reportes_filtrados = [r for r in reportes if r.fecha not in por_fecha]
        for k in por_fecha:
            r = RenglonReporte(k, None, por_fecha[k], [], None)
            reportes_filtrados.append(r)
        return sorted(reportes_filtrados, key=lambda x: x.fecha)


    @classmethod
    def generarReporte(cls, session, usuario, inicio, fin, tzone='America/Argentina/Buenos_Aires'):
        if inicio > fin:
            return []

        reportes = []
        for i in range(0, int((fin - inicio).days + 1)):
            actual = inicio + timedelta(days=i)

            q = session.query(Horario)
            q = q.filter(Horario.usuario_id == usuario['id'], Horario.dia_semanal == actual.weekday(), Horario.fecha_valido <= actual)
            q = q.order_by(Horario.fecha_valido.desc())
            horario = q.limit(1).one_or_none()

            marcaciones, duplicadas = Marcacion.obtenerMarcaciones(session, horario, usuario['id'], actual, tzone)
            marcaciones = [] if marcaciones is None else marcaciones
            justificacion = None
            r = RenglonReporte(actual, horario, marcaciones, duplicadas, justificacion)
            reportes.append(r)

        rep = Reporte(usuario, inicio, fin)
        rep.reportes = cls._agregar_marcaciones_sin_horario(session, reportes, usuario['id'], inicio, fin, tzone)

        rep.detalle = Detalle()
        rep.detalle.calcular(rep)

        return rep

    def __json__(self):
        return self.__dict__
