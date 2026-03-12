"""
Servicio para crear gastos.
"""
import re
from datetime import date
from decimal import Decimal
from typing import Optional

from app.database import db
from app.models import Gasto, Paciente, Usuario
from app.services.common.exceptions import OdontoAppError


class CrearGastoService:
    """Servicio para crear gastos."""

    _CATEGORIAS_VALIDAS = [
        'INSUMO',
        'OPERATIVO',
        'CURSO',
        'EJERCICIO_PROFESIONAL',
        'TECNICO_PROTESIS',
        'OTROS',
    ]
    _PACIENTE_TAG_REGEX = re.compile(r'^\[PACIENTE_ID:(\d+)\]\s*', re.IGNORECASE)

    @classmethod
    def _normalizar_observaciones(cls, observaciones: Optional[str], paciente_id: Optional[int]) -> Optional[str]:
        """Limpia y reescribe observaciones manteniendo un tag de paciente opcional."""
        observacion_limpia = (observaciones or '').strip()
        observacion_limpia = cls._PACIENTE_TAG_REGEX.sub('', observacion_limpia).strip()

        if paciente_id:
            prefijo = f'[PACIENTE_ID:{int(paciente_id)}] '
            return f'{prefijo}{observacion_limpia}'.strip()

        return observacion_limpia or None

    @classmethod
    def extraer_paciente_id(cls, observaciones: Optional[str]) -> Optional[int]:
        """Extrae el id de paciente desde observaciones estructuradas."""
        if not observaciones:
            return None
        match = cls._PACIENTE_TAG_REGEX.match(observaciones.strip())
        if not match:
            return None
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            return None

    @classmethod
    def limpiar_observaciones(cls, observaciones: Optional[str]) -> Optional[str]:
        """Devuelve observaciones sin el tag técnico de paciente."""
        return cls._normalizar_observaciones(observaciones, None)
    
    @staticmethod
    def crear(
        descripcion: str,
        monto: float,
        fecha: date,
        categoria: str,
        creado_por_id: int,
        observaciones: Optional[str] = None,
        comprobante: Optional[str] = None,
        paciente_id: Optional[int] = None,
    ) -> Gasto:
        """
        Crea un nuevo gasto.
        
        Args:
            descripcion: Descripción del gasto
            monto: Monto del gasto
            fecha: Fecha del gasto
            categoria: Categoría (MATERIAL, INSUMO, MATRICULA, CURSO, OPERATIVO, OTRO)
            creado_por_id: ID del usuario que crea el gasto
            observaciones: Observaciones adicionales (opcional)
            comprobante: Ruta del comprobante (opcional)
            
        Returns:
            Gasto creado
            
        Raises:
            OdontoAppError: Si los datos son inválidos
        """
        # Validar datos
        if not descripcion or descripcion.strip() == '':
            raise OdontoAppError('La descripción es requerida', codigo='DESCRIPCION_REQUERIDA')
        
        if monto <= 0:
            raise OdontoAppError('El monto debe ser mayor a 0', codigo='MONTO_INVALIDO')
        
        if categoria not in CrearGastoService._CATEGORIAS_VALIDAS:
            raise OdontoAppError(
                f'Categoría inválida. Debe ser una de: {", ".join(CrearGastoService._CATEGORIAS_VALIDAS)}',
                codigo='CATEGORIA_INVALIDA'
            )

        if categoria == 'TECNICO_PROTESIS' and not paciente_id:
            raise OdontoAppError(
                'Debe seleccionar un paciente para la categoría Técnico prótesis',
                codigo='PACIENTE_REQUERIDO'
            )

        if paciente_id:
            paciente = db.session.get(Paciente, paciente_id)
            if not paciente:
                raise OdontoAppError('Paciente no encontrado', codigo='PACIENTE_NO_ENCONTRADO')
        
        # Verificar que el usuario existe
        usuario = db.session.get(Usuario, creado_por_id)
        if not usuario:
            raise OdontoAppError('Usuario no encontrado', codigo='USUARIO_NO_ENCONTRADO')
        
        # Crear el gasto
        gasto = Gasto(
            descripcion=descripcion.strip(),
            monto=Decimal(str(monto)),
            fecha=fecha,
            categoria=categoria,
            observaciones=CrearGastoService._normalizar_observaciones(observaciones, paciente_id),
            comprobante=comprobante,
            creado_por_id=creado_por_id
        )
        
        db.session.add(gasto)
        db.session.commit()
        
        return gasto

    @staticmethod
    def actualizar(
        gasto_id: int,
        descripcion: str,
        monto: float,
        fecha: date,
        categoria: str,
        observaciones: Optional[str] = None,
        paciente_id: Optional[int] = None,
    ) -> Gasto:
        """Actualiza un gasto existente."""
        gasto = db.session.get(Gasto, gasto_id)
        if not gasto:
            raise OdontoAppError('Gasto no encontrado', codigo='GASTO_NO_ENCONTRADO')

        if not descripcion or descripcion.strip() == '':
            raise OdontoAppError('La descripción es requerida', codigo='DESCRIPCION_REQUERIDA')

        if monto <= 0:
            raise OdontoAppError('El monto debe ser mayor a 0', codigo='MONTO_INVALIDO')

        if categoria not in CrearGastoService._CATEGORIAS_VALIDAS:
            raise OdontoAppError(
                f'Categoría inválida. Debe ser una de: {", ".join(CrearGastoService._CATEGORIAS_VALIDAS)}',
                codigo='CATEGORIA_INVALIDA'
            )

        if categoria == 'TECNICO_PROTESIS' and not paciente_id:
            raise OdontoAppError(
                'Debe seleccionar un paciente para la categoría Técnico prótesis',
                codigo='PACIENTE_REQUERIDO'
            )

        if paciente_id:
            paciente = db.session.get(Paciente, paciente_id)
            if not paciente:
                raise OdontoAppError('Paciente no encontrado', codigo='PACIENTE_NO_ENCONTRADO')

        gasto.descripcion = descripcion.strip()
        gasto.monto = Decimal(str(monto))
        gasto.fecha = fecha
        gasto.categoria = categoria
        gasto.observaciones = CrearGastoService._normalizar_observaciones(observaciones, paciente_id)

        db.session.commit()
        return gasto
