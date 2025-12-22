"""
ObtenerOdontogramaService: Caso de uso para obtener/crear y consultar odontogramas.

Responsabilidades:
- Obtener odontograma actual de un paciente
- Crear odontograma vacío si no existe
- Obtener versiones específicas
- Marcar como desactualizado si hay prestaciones nuevas
- Gestionar historial de versiones (retención)
"""

from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy import func
from app.database.session import DatabaseSession
from app.models import Odontograma, Paciente, Prestacion
from app.services.common import (
    PacienteNoEncontradoError,
    OdontogramaNoEncontradoError,
)


class ObtenerOdontogramaService:
    """Caso de uso: obtener y gestionar odontogramas."""
    
    RETENCION_MAX_VERSIONES = 20  # configurable
    
    @staticmethod
    def obtener_actual(paciente_id: int) -> Tuple[Odontograma, List[Odontograma], bool, Optional[datetime]]:
        """
        Obtiene el odontograma actual de un paciente o lo crea vacío.
        
        Args:
            paciente_id: ID del paciente
        
        Returns:
            Tupla (odontograma, versiones, desactualizado, ultima_prestacion)
        
        Raises:
            PacienteNoEncontradoError: Si el paciente no existe
        """
        session = DatabaseSession.get_instance().session
        
        # Validar paciente
        paciente = session.get(Paciente, paciente_id)
        if not paciente:
            raise PacienteNoEncontradoError(paciente_id)
        
        try:
            # Obtener odontograma actual
            odontograma = session.query(Odontograma).filter_by(
                paciente_id=paciente_id, 
                es_actual=True
            ).order_by(Odontograma.version_seq.desc()).first()
            
            # Si no existe, crear vacío
            if not odontograma:
                max_version = (
                    session.query(func.max(Odontograma.version_seq))
                    .filter(Odontograma.paciente_id == paciente_id)
                    .scalar()
                ) or 0
                
                ultima_prestacion = ObtenerOdontogramaService._obtener_ultima_prestacion(session, paciente_id)
                
                odontograma = Odontograma(
                    paciente_id=paciente_id,
                    version_seq=max_version + 1,
                    es_actual=True,
                    nota_general=None,
                    creado_en=datetime.now(),
                    actualizado_en=datetime.now(),
                    ultima_prestacion_registrada_en=ultima_prestacion,
                )
                session.add(odontograma)
                session.flush()
                
                # Marcar solo este como actual
                ObtenerOdontogramaService._marcar_solo_un_actual(session, paciente_id, odontograma.id)
                session.commit()
            
            # Obtener versiones
            versiones = ObtenerOdontogramaService._obtener_versiones(session, paciente_id)
            
            # Detectar desactualización
            ultima_prestacion = ObtenerOdontogramaService._obtener_ultima_prestacion(session, paciente_id)
            desactualizado = (
                ultima_prestacion and 
                odontograma.creado_en and 
                ultima_prestacion > odontograma.creado_en
            )
            
            return odontograma, versiones, desactualizado, ultima_prestacion
            
        except Exception as exc:
            session.rollback()
            raise
    
    @staticmethod
    def obtener_version(paciente_id: int, odontograma_id: int) -> Tuple[Odontograma, List[Odontograma], bool, Optional[datetime]]:
        """
        Obtiene una versión específica de odontograma.
        
        Args:
            paciente_id: ID del paciente
            odontograma_id: ID del odontograma
        
        Returns:
            Tupla (odontograma, versiones, desactualizado, ultima_prestacion)
        
        Raises:
            OdontogramaNoEncontradoError: Si no existe la versión
        """
        session = DatabaseSession.get_instance().session
        
        try:
            odontograma = session.query(Odontograma).filter_by(
                id=odontograma_id, 
                paciente_id=paciente_id
            ).first()
            
            if not odontograma:
                raise OdontogramaNoEncontradoError(odontograma_id)
            
            versiones = ObtenerOdontogramaService._obtener_versiones(session, paciente_id)
            ultima_prestacion = ObtenerOdontogramaService._obtener_ultima_prestacion(session, paciente_id)
            
            desactualizado = (
                ultima_prestacion and 
                odontograma.creado_en and 
                ultima_prestacion > odontograma.creado_en
            )
            
            return odontograma, versiones, desactualizado, ultima_prestacion
            
        except Exception as exc:
            session.rollback()
            raise
    
    @staticmethod
    def _obtener_versiones(session, paciente_id: int) -> List[Odontograma]:
        """Obtiene todas las versiones de odontograma del paciente."""
        return session.query(Odontograma).filter_by(
            paciente_id=paciente_id
        ).order_by(Odontograma.version_seq.desc()).limit(
            ObtenerOdontogramaService.RETENCION_MAX_VERSIONES
        ).all()
    
    @staticmethod
    def _marcar_solo_un_actual(session, paciente_id: int, odontograma_id: int) -> None:
        """Marcar solo un odontograma como actual para el paciente."""
        session.query(Odontograma).filter(
            Odontograma.paciente_id == paciente_id,
            Odontograma.id != odontograma_id,
        ).update({Odontograma.es_actual: False}, synchronize_session=False)
    
    @staticmethod
    def _obtener_ultima_prestacion(session, paciente_id: int) -> Optional[datetime]:
        """Obtiene la fecha de la prestación más reciente del paciente."""
        return session.query(func.max(Prestacion.fecha)).filter(
            Prestacion.paciente_id == paciente_id
        ).scalar()
