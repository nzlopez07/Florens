"""
Servicio para eliminar prácticas.

Replica la funcionalidad de eliminar_practica() del viejo practica_service.py.
"""

from typing import Dict, Any
from app.database.session import DatabaseSession
from app.models import Practica, PrestacionPractica
from app.services.common import (
    PracticaNoEncontradaError,
    PracticaConDependenciasError,
)


class EliminarPracticaService:
    """Servicio para eliminar prácticas."""
    
    @staticmethod
    def execute(practica_id: int) -> Dict[str, Any]:
        """
        Elimina una práctica.
        
        Solo permite eliminar si la práctica no tiene prestaciones asociadas.
        
        Args:
            practica_id: ID de la práctica a eliminar
            
        Returns:
            Dict con resultado:
            {
                'success': bool,
                'mensaje': str,
            }
            
        Raises:
            PracticaNoEncontradaError: Si práctica no existe
            PracticaConDependenciasError: Si tiene prestaciones asociadas
        """
        session = DatabaseSession.get_instance().session
        
        # 1. Obtener práctica
        practica = session.query(Practica).filter(
            Practica.id == practica_id
        ).first()
        if not practica:
            raise PracticaNoEncontradaError(practica_id)
        
        # 2. Verificar que no tenga prestaciones asociadas
        prestaciones_asociadas = session.query(PrestacionPractica).filter(
            PrestacionPractica.practica_id == practica_id
        ).count()
        
        if prestaciones_asociadas > 0:
            raise PracticaConDependenciasError(
                f'No se puede eliminar la práctica "{practica.descripcion}" '
                f'porque tiene {prestaciones_asociadas} prestación(es) asociada(s)'
            )
        
        # 3. Eliminar
        session.delete(practica)
        session.commit()
        
        return {
            'success': True,
            'mensaje': f'Práctica "{practica.descripcion}" eliminada correctamente',
        }
