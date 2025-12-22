"""
Inicializador del módulo de servicios de odontograma.
"""

from .obtener_odontograma_service import ObtenerOdontogramaService
from .crear_version_odontograma_service import CrearVersionOdontogramaService

__all__ = [
    'ObtenerOdontogramaService',
    'CrearVersionOdontogramaService',
]
