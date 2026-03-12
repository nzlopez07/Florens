"""
Servicio para marcar prestación como realizada.
"""

from datetime import date
from typing import Dict, Any
from app.database.session import DatabaseSession
from app.models import Prestacion
from app.services.common import (
    OdontoAppError,
    PrestacionNoAutorizadaError,
    FechasRealizacionInvalidasError,
)


class RegistrarRealizacionPrestacionService:
    """Servicio para marcar una prestación como realizada."""
    
    @staticmethod
    def execute(prestacion_id: int, data: Dict[str, Any]) -> Prestacion:
        """
        Marca una prestación como realizada.
        
        Args:
            prestacion_id: ID de la prestación
            data: Dict con:
                - fecha_realizacion: date o str (YYYY-MM-DD)
        
        Returns:
            Prestación actualizada
            
        Raises:
            PrestacionNoAutorizadaError: Si no está autorizada
            FechasRealizacionInvalidasError: Si fecha_realizacion < fecha_autorizacion
        """
        session = DatabaseSession.get_instance().session
        
        prestacion = session.query(Prestacion).filter(
            Prestacion.id == prestacion_id
        ).first()
        
        if not prestacion:
            raise OdontoAppError(f"Prestación no encontrada (ID: {prestacion_id})")
        
        # Solo se puede realizar desde estado 'autorizada'
        if prestacion.estado != 'autorizada':
            raise OdontoAppError(
                f"Solo se pueden marcar como realizada prestaciones en estado 'autorizada'. "
                f"Esta está en estado '{prestacion.estado}'"
            )
        
        # Validar que esté autorizada (tenga fecha de autorización)
        if not prestacion.fecha_autorizacion:
            raise PrestacionNoAutorizadaError(prestacion_id)
        
        # Convertir fecha_realizacion si es string
        fecha_realizacion = data.get('fecha_realizacion')
        if isinstance(fecha_realizacion, str):
            fecha_realizacion = date.fromisoformat(fecha_realizacion)
        elif not fecha_realizacion:
            fecha_realizacion = date.today()
        
        # Validar que fecha_realizacion >= fecha_autorizacion
        if fecha_realizacion < prestacion.fecha_autorizacion:
            raise FechasRealizacionInvalidasError(
                prestacion.fecha_autorizacion, fecha_realizacion
            )
        
        # Actualizar prestación
        prestacion.fecha_realizacion = fecha_realizacion
        prestacion.estado = 'realizada'
        
        # Marcar todos los ítems pendientes como realizados con la fecha de realización
        for item in prestacion.practicas_assoc:
            if item.estado_item == 'pendiente' and not item.fecha_anulacion:
                item.estado_item = 'realizado'
                item.fecha_realizacion_item = fecha_realizacion
        
        session.commit()
        return prestacion
