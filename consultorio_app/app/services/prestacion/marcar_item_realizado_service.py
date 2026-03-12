"""
Servicio para marcar un ítem individual de práctica como realizado.
"""

from datetime import date
from typing import Dict, Any, Optional
from app.database.session import DatabaseSession
from app.models import PrestacionPractica
from app.services.common import OdontoAppError


class MarcarItemRealizadoService:
    """Marca un item individual de práctica como realizado."""

    @staticmethod
    def execute(item_id: int, data: Optional[Dict[str, Any]] = None) -> PrestacionPractica:
        """
        Marca un item de práctica como realizado.

        Args:
            item_id: ID del PrestacionPractica
            data: Dict opcional con:
                - fecha_realizacion_item: date o str (YYYY-MM-DD), default hoy

        Returns:
            PrestacionPractica actualizado

        Raises:
            OdontoAppError: Si el item no existe o ya está realizado/anulado
        """
        session = DatabaseSession.get_instance().session
        data = data or {}

        item = session.query(PrestacionPractica).filter(
            PrestacionPractica.id == item_id
        ).first()

        if not item:
            raise OdontoAppError(f"Item de práctica no encontrado (ID: {item_id})")

        if item.fecha_anulacion:
            raise OdontoAppError("No se puede marcar como realizado un ítem anulado")

        if item.estado_item == 'realizado':
            raise OdontoAppError("El ítem ya está marcado como realizado")

        fecha_realizacion_item = data.get('fecha_realizacion_item')
        if isinstance(fecha_realizacion_item, str):
            fecha_realizacion_item = date.fromisoformat(fecha_realizacion_item)
        elif not fecha_realizacion_item:
            fecha_realizacion_item = date.today()

        item.estado_item = 'realizado'
        item.fecha_realizacion_item = fecha_realizacion_item

        session.commit()
        return item
