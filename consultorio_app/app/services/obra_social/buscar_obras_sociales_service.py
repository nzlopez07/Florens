"""
BuscarObrasocialesService: Caso de uso para buscar y listar obras sociales.

Responsabilidades:
- Listar todas las obras sociales
- Buscar obras sociales por nombre
- Obtener obra social específica por ID
"""

from typing import List
from app.database.session import DatabaseSession
from app.models import ObraSocial
from app.services.common import OdontoAppError


class BuscarObrasSocialesService:
    """Caso de uso: buscar y listar obras sociales."""
    
    @staticmethod
    def listar_todas() -> List[ObraSocial]:
        """Lista todas las obras sociales ordenadas por nombre."""
        return ObraSocial.query.order_by(ObraSocial.nombre).all()
    
    @staticmethod
    def buscar_por_nombre(termino: str = None) -> List[ObraSocial]:
        """
        Busca obras sociales por nombre (búsqueda parcial, case-insensitive).
        
        Args:
            termino: Término de búsqueda (opcional)
        
        Returns:
            Lista de obras sociales que coinciden
        """
        termino = (termino or "").strip()
        
        if not termino:
            return BuscarObrasSocialesService.listar_todas()
        
        like_term = f"%{termino.lower()}%"
        return ObraSocial.query.filter(
            ObraSocial.nombre.ilike(like_term)
        ).order_by(ObraSocial.nombre).all()
    
    @staticmethod
    def obtener_por_id(obra_social_id: int) -> ObraSocial:
        """
        Obtiene una obra social por ID.
        
        Args:
            obra_social_id: ID de la obra social
        
        Returns:
            ObraSocial encontrada
        
        Raises:
            OdontoAppError: Si no existe
        """
        obra_social = ObraSocial.query.get(obra_social_id)
        if not obra_social:
            raise OdontoAppError(
                f"Obra social no encontrada (ID: {obra_social_id})",
                "OBRA_SOCIAL_NO_ENCONTRADA"
            )
        return obra_social
