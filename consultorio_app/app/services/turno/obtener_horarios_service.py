"""
Servicio para obtener horarios disponibles para agendar turnos.

Calcula slots libres en una fecha específica respetando duración deseada
y horarios de atención.
"""

from datetime import date, datetime, time, timedelta
from typing import Dict, List, Any
from app.database.session import DatabaseSession
from app.models import Turno
from app.services.common import ValidadorTurno


class ObtenerHorariosService:
    """Servicio para obtener horarios disponibles."""
    
    # Duración de cada slot de horario disponible (30 minutos)
    DURACION_SLOT = 30
    
    @staticmethod
    def obtener_horarios_disponibles(
        fecha: date,
        duracion_deseada: int = 30,
    ) -> Dict[str, Any]:
        """
        Obtiene los horarios disponibles en una fecha específica.
        
        Calcula todos los slots de 30 minutos disponibles en la fecha,
        respetando el horario de atención (8:00 a 21:00) y los turnos
        ya agendados.
        
        Args:
            fecha: Fecha para la cual obtener horarios
            duracion_deseada: Duración en minutos del turno a agendar (default 30)
            
        Returns:
            Dict con estructura:
            {
                'fecha': date,
                'horarios_disponibles': [
                    {'hora': time, 'disponible': bool, 'conflicto_con': str or None}
                ],
                'horario_inicio': time,
                'horario_fin': time,
                'duracion_deseada': int,
                'total_disponibles': int,
                'total_ocupados': int,
            }
        """
        session = DatabaseSession.get_instance().session
        
        # Validar fecha
        validacion = ValidadorTurno.validar_fecha(fecha)
        if not validacion['valido']:
            return {
                'fecha': fecha,
                'horarios_disponibles': [],
                'error': validacion['error'],
            }
        
        # Obtener horarios de atención
        horario_inicio = time(
            ValidadorTurno.HORARIO_INICIO.hour,
            ValidadorTurno.HORARIO_INICIO.minute
        )
        horario_fin = time(
            ValidadorTurno.HORARIO_FIN.hour,
            ValidadorTurno.HORARIO_FIN.minute
        )
        
        # Query turnos en la fecha
        turnos_existentes = session.query(Turno).filter(
            Turno.fecha == fecha
        ).all()
        
        # Crear lista de horarios conflictivos (bloques ocupados)
        bloques_ocupados = []
        for turno in turnos_existentes:
            inicio = turno.hora
            fin = (datetime.combine(date.today(), turno.hora) + timedelta(minutes=turno.duracion)).time()
            bloques_ocupados.append({
                'inicio': inicio,
                'fin': fin,
                'turno_id': turno.id,
                'paciente': f"{turno.paciente.nombre} {turno.paciente.apellido}",
            })
        
        # Generar todos los posibles horarios (cada 30 minutos)
        horarios_disponibles = []
        hora_actual = datetime.combine(date.today(), horario_inicio)
        hora_fin_dt = datetime.combine(date.today(), horario_fin)
        
        while hora_actual < hora_fin_dt:
            hora_slot = hora_actual.time()
            
            # Calcular hora de fin del turno con duración deseada
            hora_fin_turno = hora_actual + timedelta(minutes=duracion_deseada)
            
            # Verificar si el turno cabe dentro del horario de atención
            if hora_fin_turno.time() > horario_fin:
                # No cabe, parar
                break
            
            # Verificar solapamiento con turnos existentes
            disponible = True
            conflicto_con = None
            
            for bloque in bloques_ocupados:
                # Solapamiento si: inicio < bloque.fin AND fin > bloque.inicio
                if hora_actual.time() < bloque['fin'] and hora_fin_turno.time() > bloque['inicio']:
                    disponible = False
                    conflicto_con = bloque['paciente']
                    break
            
            horarios_disponibles.append({
                'hora': hora_slot,
                'disponible': disponible,
                'conflicto_con': conflicto_con,
            })
            
            # Avanzar al siguiente slot de 30 minutos
            hora_actual += timedelta(minutes=ObtenerHorariosService.DURACION_SLOT)
        
        # Contar disponibles y ocupados
        total_disponibles = sum(1 for h in horarios_disponibles if h['disponible'])
        total_ocupados = len(horarios_disponibles) - total_disponibles
        
        return {
            'fecha': fecha,
            'horarios_disponibles': horarios_disponibles,
            'horario_inicio': horario_inicio,
            'horario_fin': horario_fin,
            'duracion_deseada': duracion_deseada,
            'total_disponibles': total_disponibles,
            'total_ocupados': total_ocupados,
        }
    
    @staticmethod
    def obtener_proximo_horario_disponible(
        fecha: date,
        duracion_deseada: int = 30,
    ) -> Dict[str, Any]:
        """
        Obtiene el próximo horario disponible en una fecha.
        
        Args:
            fecha: Fecha a buscar
            duracion_deseada: Duración en minutos
            
        Returns:
            Dict con:
            {
                'hora': time or None,
                'disponible': bool,
                'mensaje': str,
            }
        """
        resultado = ObtenerHorariosService.obtener_horarios_disponibles(fecha, duracion_deseada)
        
        # Buscar el primer horario disponible
        for horario in resultado['horarios_disponibles']:
            if horario['disponible']:
                return {
                    'hora': horario['hora'],
                    'disponible': True,
                    'mensaje': f"Primer horario disponible: {horario['hora'].strftime('%H:%M')}",
                }
        
        # Si no hay disponibles
        return {
            'hora': None,
            'disponible': False,
            'mensaje': f"No hay horarios disponibles en {fecha.strftime('%d/%m/%Y')} para una duración de {duracion_deseada} minutos",
        }
    
    @staticmethod
    def obtener_horarios_sugeridos(
        cantidad: int = 3,
        duracion_deseada: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene horarios sugeridos para los próximos días.
        
        Busca horarios disponibles en los próximos N días y retorna
        las mejores opciones.
        
        Args:
            cantidad: Cantidad de sugerencias a retornar
            duracion_deseada: Duración en minutos
            
        Returns:
            Lista de sugerencias con estructura:
            [
                {'fecha': date, 'hora': time, 'dia_semana': str}
            ]
        """
        sugerencias = []
        fecha_actual = date.today()
        
        # Buscar en los próximos 30 días
        for dias_adelante in range(0, 30):
            if len(sugerencias) >= cantidad:
                break
            
            fecha_busqueda = fecha_actual + timedelta(days=dias_adelante)
            
            # Validar que sea día laborable
            if fecha_busqueda.weekday() >= 6:  # 5=viernes, 6=sábado, 7=domingo
                continue
            
            resultado = ObtenerHorariosService.obtener_proximo_horario_disponible(
                fecha_busqueda,
                duracion_deseada
            )
            
            if resultado['disponible']:
                dias_semana = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
                sugerencias.append({
                    'fecha': fecha_busqueda,
                    'hora': resultado['hora'],
                    'dia_semana': dias_semana[fecha_busqueda.weekday()],
                })
        
        return sugerencias
