"""
BuscarPacientesService: Caso de uso para buscar y listar pacientes.

Responsabilidades:
- Listar todos los pacientes
- Buscar pacientes por término (nombre, apellido, DNI)
- Aplicar paginación
- Obtener detalles de un paciente específico
"""

from typing import List, Dict, Any
from app.database.session import DatabaseSession
from app.models import Paciente, Turno, Prestacion
from app.services.common import PacienteNoEncontradoError


class BuscarPacientesService:
    """Caso de uso: buscar y listar pacientes."""
    
    @staticmethod
    def listar_todos() -> List[Paciente]:
        """Lista todos los pacientes ordenados por apellido y nombre."""
        return Paciente.query.order_by(Paciente.apellido, Paciente.nombre).all()
    
    @staticmethod
    def buscar(termino: str = None) -> List[Paciente]:
        """
        Busca pacientes por término (nombre, apellido o DNI).
        
        Args:
            termino: Término de búsqueda (parcial, case-insensitive)
        
        Returns:
            Lista de pacientes que coinciden
        """
        termino = (termino or "").strip()
        
        if not termino:
            return BuscarPacientesService.listar_todos()
        
        # Búsqueda en nombre, apellido y DNI
        like_term = f"%{termino.lower()}%"
        return Paciente.query.filter(
            (Paciente.nombre.ilike(like_term)) |
            (Paciente.apellido.ilike(like_term)) |
            (Paciente.dni.ilike(like_term))
        ).order_by(Paciente.apellido, Paciente.nombre).all()
    
    @staticmethod
    def obtener_por_id(paciente_id: int) -> Paciente:
        """
        Obtiene un paciente por ID.
        
        Args:
            paciente_id: ID del paciente
        
        Returns:
            Paciente encontrado
        
        Raises:
            PacienteNoEncontradoError: Si no existe
        """
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            raise PacienteNoEncontradoError(paciente_id)
        return paciente
    
    @staticmethod
    def obtener_detalle_completo(paciente_id: int) -> Dict[str, Any]:
        """
        Obtiene detalles completos de un paciente (incluye turnos, prestaciones, estadísticas).
        
        Args:
            paciente_id: ID del paciente
        
        Returns:
            Dict con paciente, turnos, prestaciones, edad y estadísticas
        
        Raises:
            PacienteNoEncontradoError: Si no existe
        """
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        paciente = BuscarPacientesService.obtener_por_id(paciente_id)
        
        # Obtener turnos recientes
        turnos = Turno.query.filter_by(paciente_id=paciente_id).order_by(
            Turno.fecha.desc(), Turno.hora.desc()
        ).limit(5).all()
        
        # Obtener prestaciones recientes
        prestaciones = Prestacion.query.filter_by(paciente_id=paciente_id).order_by(
            Prestacion.fecha.desc()
        ).limit(5).all()
        
        # Calcular edad
        edad = None
        if paciente.fecha_nac:
            edad = relativedelta(date.today(), paciente.fecha_nac).years
        
        # Contar totales
        total_turnos = Turno.query.filter_by(paciente_id=paciente_id).count()
        total_prestaciones = Prestacion.query.filter_by(paciente_id=paciente_id).count()
        
        return {
            'paciente': paciente,
            'turnos': turnos,
            'prestaciones': prestaciones,
            'edad': edad,
            'total_turnos': total_turnos,
            'total_prestaciones': total_prestaciones,
        }
