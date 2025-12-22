"""
CrearVersionOdontogramaService: Caso de uso para crear nuevas versiones de odontograma.

Responsabilidades:
- Crear nueva versión basada en la actual
- Aplicar cambios de caras
- Marcar como actual
- Gestionar historial de versiones
"""

from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy import func
from app.database.session import DatabaseSession
from app.models import Odontograma, OdontogramaCara, Paciente, Prestacion
from app.services.common import (
    PacienteNoEncontradoError,
    OdontogramaError,
    OdontogramaNoEncontradoError,
)


class CrearVersionOdontogramaService:
    """Caso de uso: crear nuevas versiones de odontograma."""
    
    RETENCION_MAX_VERSIONES = 20
    
    @staticmethod
    def execute(
        paciente_id: int,
        cambios_caras: List[dict],
        nota_general: str = None,
        base_odontograma_id: int = None,
    ) -> Tuple[Odontograma, List[Odontograma]]:
        """
        Crea una nueva versión de odontograma.
        
        Args:
            paciente_id: ID del paciente
            cambios_caras: Lista de cambios a aplicar (dicts con id_cara, prestaciones, etc)
            nota_general: Nota general para la versión
            base_odontograma_id: ID del odontograma base (si None, usa el actual)
        
        Returns:
            Tupla (odontograma_nuevo, versiones)
        
        Raises:
            PacienteNoEncontradoError: Si paciente no existe
            OdontogramaNoEncontradoError: Si base_odontograma_id no existe
            OdontogramaError: Para otros errores
        """
        session = DatabaseSession.get_instance().session
        
        try:
            # Validar paciente
            paciente = session.get(Paciente, paciente_id)
            if not paciente:
                raise PacienteNoEncontradoError(paciente_id)
            
            # Obtener odontograma base
            if base_odontograma_id:
                base = session.get(Odontograma, base_odontograma_id)
                if not base or base.paciente_id != paciente_id:
                    raise OdontogramaNoEncontradoError(base_odontograma_id)
            else:
                base = session.query(Odontograma).filter_by(
                    paciente_id=paciente_id,
                    es_actual=True
                ).first()
                if not base:
                    raise OdontogramaError("No hay odontograma base para crear versión")
            
            # Obtener siguiente número de versión
            max_version = session.query(func.max(Odontograma.version_seq)).filter(
                Odontograma.paciente_id == paciente_id
            ).scalar() or 0
            
            # Crear nueva versión
            nueva_version = Odontograma(
                paciente_id=paciente_id,
                version_seq=max_version + 1,
                es_actual=True,
                nota_general=nota_general,
                creado_en=datetime.now(),
                actualizado_en=datetime.now(),
                ultima_prestacion_registrada_en=CrearVersionOdontogramaService._obtener_ultima_prestacion(session, paciente_id),
            )
            session.add(nueva_version)
            session.flush()
            
            # Copiar caras del base y aplicar cambios
            CrearVersionOdontogramaService._copiar_y_aplicar_cambios(
                session, base, nueva_version, cambios_caras
            )
            
            # Marcar solo esta como actual
            session.query(Odontograma).filter(
                Odontograma.paciente_id == paciente_id,
                Odontograma.id != nueva_version.id,
            ).update({Odontograma.es_actual: False}, synchronize_session=False)
            
            # Aplicar retención
            CrearVersionOdontogramaService._aplicar_retencion(session, paciente_id)
            
            session.commit()
            
            # Obtener versiones
            versiones = session.query(Odontograma).filter_by(
                paciente_id=paciente_id
            ).order_by(Odontograma.version_seq.desc()).limit(
                CrearVersionOdontogramaService.RETENCION_MAX_VERSIONES
            ).all()
            
            return nueva_version, versiones
            
        except (PacienteNoEncontradoError, OdontogramaNoEncontradoError, OdontogramaError):
            session.rollback()
            raise
        except Exception as exc:
            session.rollback()
            raise OdontogramaError(f"Error al crear versión: {str(exc)}")
    
    @staticmethod
    def _copiar_y_aplicar_cambios(session, base: Odontograma, nueva: Odontograma, cambios_caras: List[dict]) -> None:
        """Copia caras del base a la nueva versión y aplica cambios."""
        # Copiar todas las caras del base
        for cara_base in base.caras:
            cara_nueva = OdontogramaCara(
                odontograma_id=nueva.id,
                id_cara=cara_base.id_cara,
                prestaciones_json=cara_base.prestaciones_json,
                anomalias_json=cara_base.anomalias_json,
            )
            session.add(cara_nueva)
        
        # Aplicar cambios (simplificado: asumir que cambios_caras contiene la estructura completa)
        # En la implementación real esto sería más complejo
        if cambios_caras:
            for cambio in cambios_caras:
                id_cara = cambio.get('id_cara')
                cara = session.query(OdontogramaCara).filter_by(
                    odontograma_id=nueva.id,
                    id_cara=id_cara
                ).first()
                if cara:
                    # Actualizar prestaciones y anomalías
                    if 'prestaciones_json' in cambio:
                        cara.prestaciones_json = cambio['prestaciones_json']
                    if 'anomalias_json' in cambio:
                        cara.anomalias_json = cambio['anomalias_json']
    
    @staticmethod
    def _aplicar_retencion(session, paciente_id: int) -> None:
        """Elimina versiones antiguas si se excede la retención."""
        ids_ordenados = [row[0] for row in session.query(Odontograma.id).filter(
            Odontograma.paciente_id == paciente_id
        ).order_by(Odontograma.version_seq.desc()).all()]
        
        if len(ids_ordenados) > CrearVersionOdontogramaService.RETENCION_MAX_VERSIONES:
            ids_a_eliminar = ids_ordenados[CrearVersionOdontogramaService.RETENCION_MAX_VERSIONES:]
            if ids_a_eliminar:
                antiguos = session.query(Odontograma).filter(Odontograma.id.in_(ids_a_eliminar)).all()
                for od in antiguos:
                    session.delete(od)
    
    @staticmethod
    def _obtener_ultima_prestacion(session, paciente_id: int) -> Optional[datetime]:
        """Obtiene la fecha de la prestación más reciente."""
        return session.query(func.max(Prestacion.fecha)).filter(
            Prestacion.paciente_id == paciente_id
        ).scalar()
