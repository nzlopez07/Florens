"""
ListarPracticasService: Caso de uso para listar y consultar prácticas.

Responsabilidades:
- Listar todas las prácticas
- Buscar prácticas por nombre o código
- Filtrar por obra social
- Obtener práctica específica
"""

from typing import List, Optional
from sqlalchemy import or_, and_
from app.database.session import DatabaseSession
from app.models import Practica
from app.models import ObraSocial


class ListarPracticasService:
    """Caso de uso: listar y consultar prácticas."""
    
    @staticmethod
    def listar_todas(incluir_bajas: bool = False) -> List[Practica]:
        """Lista todas las prácticas ordenadas por descripcion.
        
        Args:
            incluir_bajas: Si True, incluye prácticas dadas de baja. Default False.
        """
        query = Practica.query
        if not incluir_bajas:
            query = query.filter(Practica.fecha_baja.is_(None))
        return query.order_by(Practica.descripcion).all()
    
    @staticmethod
    def listar_por_proveedor(obra_social_id: Optional[int] = None, incluir_bajas: bool = False) -> List[Practica]:
        """
        Lista prácticas filtradas por proveedor.
        
        - Si obra_social_id está presente: solo prácticas de esa obra social (proveedor_tipo='OBRA_SOCIAL').
        - Si obra_social_id es None: solo prácticas particulares (proveedor_tipo='PARTICULAR').
        
        Args:
            obra_social_id: ID de obra social o None para particulares
            incluir_bajas: Si True, incluye prácticas dadas de baja. Default False.
        """
        query = Practica.query
        
        # Filtrar bajas lógicas
        if not incluir_bajas:
            query = query.filter(Practica.fecha_baja.is_(None))

        if obra_social_id is not None:
            query = query.filter(
                and_(
                    Practica.proveedor_tipo == 'OBRA_SOCIAL',
                    Practica.obra_social_id == obra_social_id,
                )
            )
        else:
            # Compatibilidad legacy: algunas prácticas "particulares" quedaron
            # guardadas como OBRA_SOCIAL apuntando a la obra social PARTICULAR.
            particular_os_ids = [
                os.id for os in ObraSocial.query.filter(ObraSocial.nombre.ilike('%PARTICULAR%')).all()
            ]
            query = query.filter(
                or_(
                    Practica.proveedor_tipo == 'PARTICULAR',
                    and_(
                        Practica.proveedor_tipo == 'OBRA_SOCIAL',
                        Practica.obra_social_id.in_(particular_os_ids) if particular_os_ids else False,
                    ),
                )
            )

        return query.order_by(Practica.descripcion).all()
    
    @staticmethod
    def buscar(termino: Optional[str] = None, obra_social_id: Optional[int] = None) -> List[Practica]:
        """
        Busca prácticas por nombre o código (case-insensitive) con filtro opcional por obra social.
        
        Args:
            termino: Término de búsqueda (opcional)
            obra_social_id: ID de obra social a filtrar (opcional)
        
        Returns:
            Lista de prácticas que coinciden
        """
        termino = (termino or "").strip()
        
        query = Practica.query
        
        # Aplicar filtro de búsqueda por término
        if termino:
            like_term = f"%{termino.lower()}%"
            query = query.filter(
                or_(
                    Practica.descripcion.ilike(like_term),
                    Practica.codigo.ilike(like_term)
                )
            )
        
        # Aplicar filtro de obra social
        if obra_social_id is not None:
            query = query.filter(
                and_(
                    Practica.proveedor_tipo == 'OBRA_SOCIAL',
                    Practica.obra_social_id == obra_social_id,
                )
            )
        else:
            particular_os_ids = [
                os.id for os in ObraSocial.query.filter(ObraSocial.nombre.ilike('%PARTICULAR%')).all()
            ]
            query = query.filter(
                or_(
                    Practica.proveedor_tipo == 'PARTICULAR',
                    and_(
                        Practica.proveedor_tipo == 'OBRA_SOCIAL',
                        Practica.obra_social_id.in_(particular_os_ids) if particular_os_ids else False,
                    ),
                )
            )
        
        return query.order_by(Practica.descripcion).all()
    
    @staticmethod
    def obtener_por_id(practica_id: int) -> Practica:
        """
        Obtiene una práctica por ID.
        
        Args:
            practica_id: ID de la práctica
        
        Returns:
            Práctica encontrada
        
        Raises:
            PracticaNoEncontradaError: Si no existe
        """
        from app.services.common import PracticaNoEncontradaError
        
        practica = Practica.query.get(practica_id)
        if not practica:
            raise PracticaNoEncontradaError(practica_id)
        return practica
    
    @staticmethod
    def obtener_por_codigo(codigo: str) -> Practica:
        """
        Obtiene una práctica por código.
        
        Args:
            codigo: Código de la práctica
        
        Returns:
            Práctica encontrada
        
        Raises:
            PracticaNoEncontradaError: Si no existe
        """
        from app.services.common import PracticaNoEncontradaError
        
        practica = Practica.query.filter_by(codigo=codigo).first()
        if not practica:
            raise PracticaNoEncontradaError(practica_id=None, razon=f"Código: {codigo}")
        return practica
