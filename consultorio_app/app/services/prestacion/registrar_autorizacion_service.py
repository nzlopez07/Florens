"""
Servicio para registrar autorización de prestaciones IPSS.
"""

from datetime import datetime, date
from typing import Dict, Any, Optional
from app.database.session import DatabaseSession
from app.models import Prestacion
from app.services.common import (
    OdontoAppError,
    EstadoPrestacionInvalidoError,
)


class RegistrarAutorizacionPrestacionService:
    """Servicio para registrar autorización de una prestación."""
    
    @staticmethod
    def execute(prestacion_id: int, data: Dict[str, Any]) -> Prestacion:
        """
        Registra la autorización de una prestación.
        
        Args:
            prestacion_id: ID de la prestación
            data: Dict con:
                - fecha_autorizacion: date o str (YYYY-MM-DD)
                - importe_profesional_autorizado: float (requerido)
                - importe_afiliado_autorizado: float (requerido)
                - importe_coseguro_autorizado: float (opcional)
                - autorizacion_adjunta_path: str (opcional, ruta del archivo)
                - observaciones_autorizacion: str (opcional)
        
        Returns:
            Prestación actualizada
            
        Raises:
            EstadoPrestacionInvalidoError: Si no está en estado 'borrador'
        """
        session = DatabaseSession.get_instance().session
        
        prestacion = session.query(Prestacion).filter(
            Prestacion.id == prestacion_id
        ).first()
        
        if not prestacion:
            raise OdontoAppError(f"Prestación no encontrada (ID: {prestacion_id})")
        
        # Solo se puede autorizar desde estado 'borrador'
        if prestacion.estado != 'borrador':
            raise EstadoPrestacionInvalidoError(prestacion.estado, 'autorizada')
        
        # Convertir fecha_autorizacion si es string
        fecha_autorizacion = data.get('fecha_autorizacion')
        if isinstance(fecha_autorizacion, str):
            fecha_autorizacion = date.fromisoformat(fecha_autorizacion)
        elif not fecha_autorizacion:
            fecha_autorizacion = date.today()
        
        # Registrar autorización
        prestacion.fecha_autorizacion = fecha_autorizacion
        prestacion.importe_profesional_autorizado = float(
            data.get('importe_profesional_autorizado', 0)
        )
        prestacion.importe_afiliado_autorizado = float(
            data.get('importe_afiliado_autorizado', 0)
        )
        
        if data.get('importe_coseguro_autorizado'):
            prestacion.importe_coseguro_autorizado = float(
                data['importe_coseguro_autorizado']
            )
        
        if data.get('autorizacion_adjunta_path'):
            prestacion.autorizacion_adjunta_path = data['autorizacion_adjunta_path']
        
        observaciones = data.get('observaciones_autorizacion', '').strip()
        if observaciones:
            prestacion.observaciones_autorizacion = observaciones
        
        # Cambiar estado a 'autorizada'
        prestacion.estado = 'autorizada'
        
        session.commit()
        return prestacion
