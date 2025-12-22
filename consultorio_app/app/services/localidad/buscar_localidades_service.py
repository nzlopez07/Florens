"""
BuscarLocalidadesService: Caso de uso para buscar y listar localidades.

Responsabilidades:
- Listar todas las localidades
- Buscar localidades por nombre (filtro)
- Obtener localidad específica por ID
"""

from typing import List
from sqlalchemy import func
from app.database.session import DatabaseSession
from app.models import Localidad
from app.services.common import LocalidadNoEncontradaError


class BuscarLocalidadesService:
    """Caso de uso: buscar y listar localidades."""
    
    @staticmethod
    def listar_todas() -> List[Localidad]:
        """Lista todas las localidades ordenadas por nombre."""
        return Localidad.query.order_by(Localidad.nombre).all()
    
    @staticmethod
    def buscar_por_nombre(termino: str = None) -> List[Localidad]:
        """
        Busca localidades por nombre (búsqueda parcial, case-insensitive).
        
        Args:
            termino: Término de búsqueda (opcional)
        
        Returns:
            Lista de localidades que coinciden
        """
        termino = (termino or "").strip()
        
        if not termino:
            return BuscarLocalidadesService.listar_todas()
        
        like_term = f"%{termino.lower()}%"
        return Localidad.query.filter(
            Localidad.nombre.ilike(like_term)
        ).order_by(Localidad.nombre).all()
    
    @staticmethod
    def obtener_por_id(localidad_id: int) -> Localidad:
        """
        Obtiene una localidad por ID.
        
        Args:
            localidad_id: ID de la localidad
        
        Returns:
            Localidad encontrada
        
        Raises:
            LocalidadNoEncontradaError: Si no existe
        """
        localidad = Localidad.query.get(localidad_id)
        if not localidad:
            raise LocalidadNoEncontradaError(localidad_id=localidad_id)
        return localidad
    
    @staticmethod
    def obtener_por_nombre(nombre: str) -> Localidad:
        """
        Obtiene una localidad por nombre (búsqueda exacta, case-insensitive).
        
        Args:
            nombre: Nombre de la localidad
        
        Returns:
            Localidad encontrada
        
        Raises:
            LocalidadNoEncontradaError: Si no existe
        """
        localidad = Localidad.query.filter(
            func.lower(Localidad.nombre) == nombre.lower()
        ).first()
        
        if not localidad:
            raise LocalidadNoEncontradaError(nombre=nombre)
        return localidad
