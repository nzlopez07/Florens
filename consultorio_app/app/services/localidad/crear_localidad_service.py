"""
CrearLocalidadService: Caso de uso para crear una nueva localidad.

Responsabilidades:
- Validar nombre de localidad
- Normalizar nombre (evitar duplicados por mayúsculas/espacios)
- Verificar que no exista localidad con mismo nombre (case-insensitive)
- Crear y persistir localidad
"""

from sqlalchemy import func
from app.database.session import DatabaseSession
from app.models import Localidad
from app.services.common import (
    LocalidadError,
    DatosInvalidosPacienteError,
    ValidadorLocalidad,
)


class CrearLocalidadService:
    """Caso de uso: crear una nueva localidad."""
    
    @staticmethod
    def execute(nombre: str) -> Localidad:
        """
        Crea una nueva localidad.
        
        Args:
            nombre: Nombre de la localidad (requerido)
        
        Returns:
            Localidad creada
        
        Raises:
            DatosInvalidosPacienteError: Si el nombre es inválido
            LocalidadError: Si ya existe una localidad con ese nombre
        """
        # Validar nombre
        if not ValidadorLocalidad.validar_nombre(nombre):
            raise DatosInvalidosPacienteError("localidad_nombre", "El nombre no puede estar vacío")
        
        # Normalizar nombre
        nombre_norm = ValidadorLocalidad.normalizar_nombre(nombre)
        
        session = DatabaseSession.get_instance().session
        
        try:
            # Verificar que no exista (case-insensitive)
            existente = Localidad.query.filter(
                func.lower(Localidad.nombre) == nombre_norm.lower()
            ).first()
            
            if existente:
                return existente  # Retornar existente si ya está
            
            # Crear nueva localidad
            localidad = Localidad(nombre=nombre_norm)
            session.add(localidad)
            session.commit()
            return localidad
            
        except Exception as exc:
            session.rollback()
            raise LocalidadError(f"Error al crear localidad: {str(exc)}")
    
    @staticmethod
    def obtener_o_crear(nombre: str) -> Localidad:
        """
        Obtiene una localidad existente o la crea si no existe.
        
        Args:
            nombre: Nombre de la localidad
        
        Returns:
            Localidad existente o nueva
        """
        return CrearLocalidadService.execute(nombre)
