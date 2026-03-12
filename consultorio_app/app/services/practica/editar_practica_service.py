"""
Servicio para editar prácticas existentes.

Replica la funcionalidad de actualizar_practica() del viejo practica_service.py.
"""

from typing import Dict, Any, Optional
from app.database.session import DatabaseSession
from app.models import Practica, ObraSocial
from app.services.common import (
    PracticaNoEncontradaError,
    ObraSocialNoEncontradaError,
    DatosInvalidosError,
)


class EditarPracticaService:
    """Servicio para editar prácticas existentes."""
    
    TIPOS_PROVEEDOR = ['OBRA_SOCIAL', 'PARTICULAR']
    
    @staticmethod
    def execute(practica_id: int, data: Dict[str, Any]) -> Practica:
        """
        Edita una práctica existente.
        
        Args:
            practica_id: ID de la práctica a editar
            data: Dict con campos a actualizar:
            {
                'codigo': str,                  # OPCIONAL
                'descripcion': str,             # OPCIONAL
                'monto_unitario': float,        # OPCIONAL
                'proveedor_tipo': str,          # OPCIONAL
                'obra_social_id': int,          # OPCIONAL
            }
            
        Returns:
            Objeto Practica actualizado
            
        Raises:
            PracticaNoEncontradaError: Si practica no existe
            DatosInvalidosError: Si valor inválido
        """
        session = DatabaseSession.get_instance().session
        
        # 1. Obtener práctica
        practica = session.query(Practica).filter(
            Practica.id == practica_id
        ).first()
        if not practica:
            raise PracticaNoEncontradaError(practica_id)
        
        # 2. Actualizar campos opcionalmente
        
        # Código
        if 'codigo' in data:
            codigo_original = data.get('codigo', '').strip().upper()
            if codigo_original:
                # Obtener es_plus (mantener el valor actual si no se especifica)
                es_plus = data.get('es_plus', practica.es_plus)
                
                # Si es plus, prefijar con 'plus_'
                codigo = f'plus_{codigo_original}' if es_plus else codigo_original
                
                # Verificar que no exista otro con el mismo código en el mismo proveedor/obra_social
                proveedor_tipo_actual = data.get('proveedor_tipo', practica.proveedor_tipo).strip().upper()
                obra_social_id_actual = data.get('obra_social_id', practica.obra_social_id)
                if not obra_social_id_actual or proveedor_tipo_actual == 'PARTICULAR':
                    obra_social_id_actual = None
                existe_otro = session.query(Practica).filter(
                    Practica.codigo == codigo,
                    Practica.proveedor_tipo == proveedor_tipo_actual,
                    Practica.obra_social_id == obra_social_id_actual,
                    Practica.id != practica_id
                ).first()
                if existe_otro:
                    raise DatosInvalidosError(f'Ya existe otra práctica con código {codigo} para este proveedor')
                practica.codigo = codigo
        
        # Es Plus (solo permitir cambio al crear, pero si se envía, actualizar)
        if 'es_plus' in data:
            practica.es_plus = data.get('es_plus', False)
        
        # Descripción
        if 'descripcion' in data:
            descripcion = data.get('descripcion', '').strip()
            if not descripcion:
                raise DatosInvalidosError('descripcion no puede estar vacía')
            practica.descripcion = descripcion
        
        # Monto unitario
        if 'monto_unitario' in data:
            try:
                monto = float(data.get('monto_unitario'))
            except (ValueError, TypeError):
                raise DatosInvalidosError('monto_unitario debe ser un número')
            
            if monto <= 0:
                raise DatosInvalidosError('monto_unitario debe ser mayor a 0')
            
            practica.monto_unitario = monto
        
        # Proveedor tipo
        if 'proveedor_tipo' in data:
            proveedor_tipo = data.get('proveedor_tipo', '').strip().upper()
            if proveedor_tipo not in EditarPracticaService.TIPOS_PROVEEDOR:
                raise DatosInvalidosError(
                    f'proveedor_tipo debe ser uno de: {", ".join(EditarPracticaService.TIPOS_PROVEEDOR)}'
                )
            practica.proveedor_tipo = proveedor_tipo
        
        # Obra social ID
        if 'obra_social_id' in data:
            obra_social_id = data.get('obra_social_id')
            if not obra_social_id:
                obra_social_id = None
            
            # Si es OBRA_SOCIAL, validar obra_social_id
            if practica.proveedor_tipo == 'OBRA_SOCIAL':
                if not obra_social_id:
                    raise DatosInvalidosError('obra_social_id es requerido para proveedor_tipo OBRA_SOCIAL')
                
                obra_social = session.query(ObraSocial).filter(
                    ObraSocial.id == obra_social_id
                ).first()
                if not obra_social:
                    raise ObraSocialNoEncontradaError(obra_social_id)
                
                practica.obra_social_id = obra_social_id
            else:
                # PARTICULAR: no debe tener obra_social_id
                practica.obra_social_id = None
        
        session.commit()
        return practica
