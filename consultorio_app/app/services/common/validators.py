"""
Validadores comunes reutilizables en los services.

Estos validadores encapsulan reglas de negocio simples y pueden ser
utilizados por múltiples services sin duplicar código.
"""

from datetime import date, time
import re


class ValidadorPaciente:
    """Validadores para datos de paciente."""
    
    @staticmethod
    def validar_dni(dni: str) -> bool:
        """Valida que el DNI sea válido (8 dígitos)."""
        if not dni:
            return False
        dni_limpio = dni.strip().replace(".", "").replace("-", "")
        return dni_limpio.isdigit() and len(dni_limpio) == 8
    
    @staticmethod
    def validar_nombre(nombre: str) -> bool:
        """Valida que el nombre no esté vacío."""
        return bool(nombre and nombre.strip())
    
    @staticmethod
    def validar_apellido(apellido: str) -> bool:
        """Valida que el apellido no esté vacío."""
        return bool(apellido and apellido.strip())
    
    @staticmethod
    def validar_telefono(telefono: str) -> bool:
        """Valida formato básico de teléfono (opcional, pero si se proporciona, debe ser válido)."""
        if not telefono:
            return True  # teléfono es opcional
        telefono_limpio = telefono.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        return telefono_limpio.isdigit() and len(telefono_limpio) >= 7


class ValidadorTurno:
    """Validadores para datos de turno."""
    
    HORARIO_INICIO = time(8, 0)
    HORARIO_FIN = time(21, 0)
    DURACION_MIN = 5
    DURACION_MAX = 480
    DIAS_LABORABLES = [0, 1, 2, 3, 4, 5]  # Lunes a Sábado
    
    @staticmethod
    def validar_fecha(fecha: date) -> tuple:
        """Valida que la fecha sea válida (no pasada, día laborable).
        
        Returns:
            (es_válida, mensaje_error)
        """
        if fecha < date.today():
            return False, "No se pueden agendar turnos en fechas pasadas"
        
        if fecha.weekday() not in ValidadorTurno.DIAS_LABORABLES:
            return False, "Los turnos solo se pueden agendar de lunes a sábado"
        
        return True, None
    
    @staticmethod
    def validar_hora(hora: time) -> tuple:
        """Valida que la hora esté dentro del horario de atención.
        
        Returns:
            (es_válida, mensaje_error)
        """
        if hora < ValidadorTurno.HORARIO_INICIO or hora >= ValidadorTurno.HORARIO_FIN:
            return False, (
                f"Los turnos solo se pueden agendar entre "
                f"{ValidadorTurno.HORARIO_INICIO.strftime('%H:%M')} y "
                f"{ValidadorTurno.HORARIO_FIN.strftime('%H:%M')}"
            )
        return True, None
    
    @staticmethod
    def validar_duracion(duracion: int) -> tuple:
        """Valida que la duración esté en rango válido.
        
        Returns:
            (es_válida, mensaje_error)
        """
        if duracion < ValidadorTurno.DURACION_MIN or duracion > ValidadorTurno.DURACION_MAX:
            return False, (
                f"La duración debe estar entre {ValidadorTurno.DURACION_MIN} y "
                f"{ValidadorTurno.DURACION_MAX} minutos"
            )
        return True, None


class ValidadorLocalidad:
    """Validadores para datos de localidad."""
    
    @staticmethod
    def normalizar_nombre(nombre: str) -> str:
        """Normaliza el nombre de localidad (comprime espacios, Title Case)."""
        if not nombre:
            return ""
        limpio = ' '.join(nombre.strip().split())
        return limpio.title()
    
    @staticmethod
    def validar_nombre(nombre: str) -> bool:
        """Valida que el nombre no esté vacío."""
        return bool(nombre and nombre.strip())
