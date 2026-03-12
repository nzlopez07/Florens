"""
Servicio para dar de baja prácticas (baja lógica).

Replica la funcionalidad de eliminar_practica() del viejo practica_service.py,
pero implementa baja lógica en lugar de eliminación física.
"""

from typing import Dict, Any
from datetime import date
from app.database.session import DatabaseSession
from app.models import Practica, PrestacionPractica
from app.services.common import (
    PracticaNoEncontradaError,
    PracticaConDependenciasError,
    DatosInvalidosError,
)


class EliminarPracticaService:
    """Servicio para dar de baja prácticas (baja lógica)."""
    
    @staticmethod
    def execute(practica_id: int, razon: str = None) -> Dict[str, Any]:
        """
        Da de baja una práctica (baja lógica).
        
        Marca la práctica con fecha_baja y razón, en lugar de eliminarla.
        Esto permite mantener el historial incluso si tiene prestaciones asociadas.
        
        Args:
            practica_id: ID de la práctica a dar de baja
            razon: Razón de la baja (opcional)
            
        Returns:
            Dict con resultado:
            {
                'success': bool,
                'mensaje': str,
            }
            
        Raises:
            PracticaNoEncontradaError: Si práctica no existe
            DatosInvalidosError: Si la práctica ya está dada de baja
        """
        session = DatabaseSession.get_instance().session
        
        # 1. Obtener práctica
        practica = session.query(Practica).filter(
            Practica.id == practica_id
        ).first()
        if not practica:
            raise PracticaNoEncontradaError(practica_id)
        
        # 2. Verificar que no esté ya dada de baja
        if practica.fecha_baja:
            raise DatosInvalidosError(
                f'La práctica "{practica.descripcion}" ya fue dada de baja el {practica.fecha_baja}'
            )
        
        # 3. Dar de baja (baja lógica)
        practica.fecha_baja = date.today()
        practica.razon_baja = razon or 'Baja solicitada por usuario'
        practica.activa = False
        
        session.commit()
        
        # 4. Informar si tiene prestaciones asociadas
        prestaciones_asociadas = session.query(PrestacionPractica).filter(
            PrestacionPractica.practica_id == practica_id,
            PrestacionPractica.fecha_anulacion.is_(None)
        ).count()
        
        mensaje = f'Práctica "{practica.descripcion}" dada de baja correctamente'
        if prestaciones_asociadas > 0:
            mensaje += f' (mantiene {prestaciones_asociadas} prestación(es) asociada(s) en el historial)'
        
        return {
            'success': True,
            'mensaje': mensaje,
        }
