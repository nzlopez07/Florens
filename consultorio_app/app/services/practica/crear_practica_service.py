"""
Servicio para crear nuevas prácticas.

Replica la funcionalidad de crear_practica() del viejo practica_service.py.
"""

from typing import Dict, Any
from app.database.session import DatabaseSession
from app.models import Practica, ObraSocial
from app.services.common import (
    ObraSocialNoEncontradaError,
    DatosInvalidosError,
)


class CrearPracticaService:
    """Servicio para crear prácticas nuevas."""
    
    # Tipos de proveedor válidos
    TIPOS_PROVEEDOR = ['OBRA_SOCIAL', 'PARTICULAR']
    
    @staticmethod
    def execute(data: Dict[str, Any]) -> Practica:
        """
        Crea una nueva práctica.
        
        Args:
            data: Dict con estructura:
            {
                'codigo': str,                  # REQUERIDO, único
                'descripcion': str,             # REQUERIDO
                'monto_unitario': float,        # REQUERIDO, > 0
                'proveedor_tipo': str,          # REQUERIDO ('OBRA_SOCIAL' o 'PARTICULAR')
                'obra_social_id': int,          # REQUERIDO si proveedor_tipo='OBRA_SOCIAL'
            }
            
        Returns:
            Objeto Practica creado
            
        Raises:
            DatosInvalidosError: Si falta campo requerido o valor inválido
            ObraSocialNoEncontradaError: Si obra_social_id no existe
        """
        session = DatabaseSession.get_instance().session
        
        # 1. Validar y extraer datos requeridos
        codigo = data.get('codigo', '').strip().upper()
        if not codigo:
            raise DatosInvalidosError('codigo es requerido')
        
        descripcion = data.get('descripcion', '').strip()
        if not descripcion:
            raise DatosInvalidosError('descripcion es requerida')
        
        try:
            monto_unitario = float(data.get('monto_unitario', 0))
        except (ValueError, TypeError):
            raise DatosInvalidosError('monto_unitario debe ser un número')
        
        if monto_unitario <= 0:
            raise DatosInvalidosError('monto_unitario debe ser mayor a 0')
        
        proveedor_tipo = data.get('proveedor_tipo', '').strip().upper()
        if proveedor_tipo not in CrearPracticaService.TIPOS_PROVEEDOR:
            raise DatosInvalidosError(
                f'proveedor_tipo debe ser uno de: {", ".join(CrearPracticaService.TIPOS_PROVEEDOR)}'
            )
        
        obra_social_id = data.get('obra_social_id')
        
        # 2. Validar que código no exista
        existente = session.query(Practica).filter(
            Practica.codigo == codigo
        ).first()
        if existente:
            raise DatosInvalidosError(f'Ya existe una práctica con código {codigo}')
        
        # 3. Si es OBRA_SOCIAL, validar obra_social_id
        if proveedor_tipo == 'OBRA_SOCIAL':
            if not obra_social_id:
                raise DatosInvalidosError('obra_social_id es requerido para proveedor_tipo OBRA_SOCIAL')
            
            obra_social = session.query(ObraSocial).filter(
                ObraSocial.id == obra_social_id
            ).first()
            if not obra_social:
                raise ObraSocialNoEncontradaError(obra_social_id)
        else:
            # PARTICULAR: obra_social_id no debe usarse
            obra_social_id = None
        
        # 4. Crear Practica
        practica = Practica(
            codigo=codigo,
            descripcion=descripcion,
            monto_unitario=monto_unitario,
            proveedor_tipo=proveedor_tipo,
            obra_social_id=obra_social_id,
        )
        session.add(practica)
        session.commit()
        
        return practica
