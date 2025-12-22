"""
EditarPacienteService: Caso de uso para editar un paciente existente.

Responsabilidades:
- Validar datos del paciente
- Verificar que el paciente exista
- Validar cambios de DNI (no duplicado)
- Actualizar y persistir cambios
"""

from datetime import date
from sqlalchemy import func
from app.database.session import DatabaseSession
from app.models import Paciente, Localidad
from app.services.common import (
    PacienteError,
    PacienteNoEncontradoError,
    PacienteDuplicadoError,
    DatosInvalidosPacienteError,
    LocalidadNoEncontradaError,
    ValidadorPaciente,
)


class EditarPacienteService:
    """Caso de uso: editar un paciente existente."""
    
    @staticmethod
    def execute(
        paciente_id: int,
        nombre: str = None,
        apellido: str = None,
        dni: str = None,
        fecha_nac: date = None,
        telefono: str = None,
        direccion: str = None,
        barrio: str = None,
        localidad_nombre: str = None,
        localidad_id: int = None,
        obra_social_id: int = None,
        nro_afiliado: str = None,
        titular: str = None,
        parentesco: str = None,
        lugar_trabajo: str = None,
    ) -> Paciente:
        """
        Edita un paciente existente.
        
        Args:
            paciente_id: ID del paciente a editar (requerido)
            (resto de args: solo se actualizan si se proporcionan)
        
        Returns:
            Paciente actualizado
        
        Raises:
            PacienteNoEncontradoError: Si el paciente no existe
            DatosInvalidosPacienteError: Si algún dato es inválido
            PacienteDuplicadoError: Si se intenta cambiar a un DNI duplicado
        """
        session = DatabaseSession.get_instance().session
        
        try:
            # Obtener paciente existente
            paciente = Paciente.query.get(paciente_id)
            if not paciente:
                raise PacienteNoEncontradoError(paciente_id)
            
            # Validar y actualizar nombre
            if nombre is not None:
                if not ValidadorPaciente.validar_nombre(nombre):
                    raise DatosInvalidosPacienteError("nombre", "El nombre no puede estar vacío")
                paciente.nombre = nombre.strip()
            
            # Validar y actualizar apellido
            if apellido is not None:
                if not ValidadorPaciente.validar_apellido(apellido):
                    raise DatosInvalidosPacienteError("apellido", "El apellido no puede estar vacío")
                paciente.apellido = apellido.strip()
            
            # Validar y actualizar DNI (verificar duplicado)
            if dni is not None:
                if not ValidadorPaciente.validar_dni(dni):
                    raise DatosInvalidosPacienteError("dni", "DNI inválido. Debe tener 8 dígitos")
                
                dni_limpio = dni.strip().replace(".", "").replace("-", "")
                
                # Verificar duplicado (excluyendo el paciente actual)
                otro_con_dni = Paciente.query.filter(
                    Paciente.dni == dni_limpio,
                    Paciente.id != paciente_id
                ).first()
                if otro_con_dni:
                    raise PacienteDuplicadoError(dni_limpio)
                
                paciente.dni = dni_limpio
            
            # Actualizar fecha nacimiento
            if fecha_nac is not None:
                paciente.fecha_nac = fecha_nac
            
            # Validar y actualizar teléfono
            if telefono is not None:
                if telefono and not ValidadorPaciente.validar_telefono(telefono):
                    raise DatosInvalidosPacienteError("telefono", "Formato de teléfono inválido")
                paciente.telefono = telefono.strip() if telefono else None
            
            # Actualizar dirección
            if direccion is not None:
                paciente.direccion = direccion.strip() if direccion else None
            
            # Actualizar barrio
            if barrio is not None:
                paciente.barrio = barrio.strip() if barrio else None
            
            # Resolver localidad
            if localidad_nombre or localidad_id:
                if localidad_nombre:
                    localidad = EditarPacienteService._obtener_o_crear_localidad(localidad_nombre)
                    paciente.localidad_id = localidad.id
                elif localidad_id:
                    localidad = Localidad.query.get(localidad_id)
                    if not localidad:
                        raise LocalidadNoEncontradaError(localidad_id=localidad_id)
                    paciente.localidad_id = localidad_id
            
            # Actualizar obra social
            if obra_social_id is not None:
                paciente.obra_social_id = obra_social_id
            
            # Actualizar campos de obra social
            if nro_afiliado is not None:
                paciente.nro_afiliado = nro_afiliado.strip() if nro_afiliado else None
            if titular is not None:
                paciente.titular = titular.strip() if titular else None
            if parentesco is not None:
                paciente.parentesco = parentesco.strip() if parentesco else None
            
            # Actualizar lugar de trabajo
            if lugar_trabajo is not None:
                paciente.lugar_trabajo = lugar_trabajo.strip() if lugar_trabajo else None
            
            session.commit()
            return paciente
            
        except (PacienteNoEncontradoError, DatosInvalidosPacienteError, 
                PacienteDuplicadoError, LocalidadNoEncontradaError):
            session.rollback()
            raise
        except Exception as exc:
            session.rollback()
            raise PacienteError(f"Error al editar paciente: {str(exc)}")
    
    @staticmethod
    def _obtener_o_crear_localidad(nombre: str) -> Localidad:
        """Obtiene o crea una localidad por nombre (case-insensitive)."""
        from app.services.common import ValidadorLocalidad
        
        nombre_norm = ValidadorLocalidad.normalizar_nombre(nombre)
        if not nombre_norm:
            raise DatosInvalidosPacienteError("localidad_nombre", "El nombre de localidad no puede estar vacío")
        
        session = DatabaseSession.get_instance().session
        
        existente = Localidad.query.filter(
            func.lower(Localidad.nombre) == nombre_norm.lower()
        ).first()
        
        if existente:
            return existente
        
        nueva = Localidad(nombre=nombre_norm)
        session.add(nueva)
        session.commit()
        return nueva
