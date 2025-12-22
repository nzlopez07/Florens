"""
Inicializador del módulo de servicios de localidad.
"""

from .buscar_localidades_service import BuscarLocalidadesService
from .crear_localidad_service import CrearLocalidadService

__all__ = [
    'BuscarLocalidadesService',
    'CrearLocalidadService',
]
