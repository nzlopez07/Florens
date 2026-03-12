"""
Servicio para registrar cobros en prestaciones IPSS.
"""

from datetime import date
from typing import Dict, Any
from app.database.session import DatabaseSession
from app.models import Prestacion, PrestacionCobro
from app.services.common import OdontoAppError


class RegistrarCobroPrestacionService:
    """Servicio para registrar un cobro en una prestación."""
    
    @staticmethod
    def execute(prestacion_id: int, data: Dict[str, Any]) -> PrestacionCobro:
        """
        Registra un cobro en una prestación.
        
        Args:
            prestacion_id: ID de la prestación
            data: Dict con:
                - fecha_cobro: date o str (YYYY-MM-DD)
                - tipo_cobro: str (requerido) - plus_consulta, plus_practica, plus_afiliado, honorario_os, otro
                - monto: float (requerido)
                - razon: str (opcional)
                - usuario_id: int (opcional)
        
        Returns:
            Objeto PrestacionCobro creado
            
        Raises:
            OdontoAppError: Si prestación no existe o no está en estado válido
        """
        session = DatabaseSession.get_instance().session
        
        prestacion = session.query(Prestacion).filter(
            Prestacion.id == prestacion_id
        ).first()
        
        if not prestacion:
            raise OdontoAppError(f"Prestación no encontrada (ID: {prestacion_id})")
        
        # Permitir cobros en estados 'autorizada' y 'realizada'
        if prestacion.estado not in ['autorizada', 'realizada']:
            raise OdontoAppError(
                f"No se pueden registrar cobros en una prestación en estado '{prestacion.estado}'"
            )
        
        # Convertir fecha_cobro si es string
        fecha_cobro = data.get('fecha_cobro')
        if isinstance(fecha_cobro, str):
            fecha_cobro = date.fromisoformat(fecha_cobro)
        elif not fecha_cobro:
            fecha_cobro = date.today()
        
        # Crear cobro
        cobro = PrestacionCobro(
            prestacion_id=prestacion_id,
            fecha_cobro=fecha_cobro,
            tipo_cobro=data.get('tipo_cobro'),
            monto=float(data.get('monto', 0)),
            razon=data.get('razon', '').strip() or None,
            usuario_id=data.get('usuario_id'),
        )
        
        session.add(cobro)
        session.commit()
        return cobro
