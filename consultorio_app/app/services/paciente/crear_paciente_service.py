"""
CrearPacienteService: Caso de uso para crear un nuevo paciente.

Responsabilidades:
- Validar datos del paciente
- Verificar que no exista paciente con el mismo DNI
- Crear y persistir el paciente
- Manejar transacciones y errores de negocio

No debe:
- Importar Flask
- Conocer detalles de HTTP
"""

from datetime import date
from sqlalchemy import func
from app.database.session import DatabaseSession
from app.models import Paciente, Localidad
from app.services.common import (
    PacienteError,
    PacienteDuplicadoError,
    DatosInvalidosPacienteError,
    LocalidadNoEncontradaError,
    ValidadorPaciente,
)


class CrearPacienteService:
    """Caso de uso: crear un nuevo paciente."""
    
    @staticmethod
    def execute(
        nombre: str,
        apellido: str,
        dni: str,
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
        Crea un nuevo paciente con validación completa.
        
        Args:
            nombre: Nombre del paciente (requerido)
            apellido: Apellido del paciente (requerido)
            dni: DNI del paciente (requerido, debe ser único)
            fecha_nac: Fecha de nacimiento (opcional)
            telefono: Teléfono (opcional)
            direccion: Dirección (opcional)
            barrio: Barrio (opcional)
            localidad_nombre: Nombre de localidad (si se proporciona, se crea/busca)
            localidad_id: ID de localidad existente (alternativa a localidad_nombre)
            obra_social_id: ID de obra social (opcional)
            nro_afiliado: Número de afiliado (opcional)
            titular: Nombre del titular (opcional)
            parentesco: Parentesco con titular (opcional)
            lugar_trabajo: Lugar de trabajo (opcional)
        
        Returns:
            Paciente creado
        
        Raises:
            DatosInvalidosPacienteError: Si algún dato es inválido
            PacienteDuplicadoError: Si ya existe paciente con ese DNI
            LocalidadNoEncontradaError: Si localidad_id no existe
            PacienteError: Para otros errores de negocio
        """
        # Validar datos requeridos
        if not ValidadorPaciente.validar_nombre(nombre):
            raise DatosInvalidosPacienteError("nombre", "El nombre no puede estar vacío")
        
        if not ValidadorPaciente.validar_apellido(apellido):
            raise DatosInvalidosPacienteError("apellido", "El apellido no puede estar vacío")
        
        if not ValidadorPaciente.validar_dni(dni):
            raise DatosInvalidosPacienteError("dni", "DNI inválido. Debe tener 8 dígitos")
        
        if telefono and not ValidadorPaciente.validar_telefono(telefono):
            raise DatosInvalidosPacienteError("telefono", "Formato de teléfono inválido")
        
        session = DatabaseSession.get_instance().session
        
        try:
            # Verificar que no exista paciente con ese DNI
            dni_limpio = dni.strip().replace(".", "").replace("-", "")
            existente = Paciente.query.filter_by(dni=dni_limpio).first()
            if existente:
                raise PacienteDuplicadoError(dni_limpio)
            
            # Resolver localidad
            localidad_id_final = None
            if localidad_nombre:
                localidad = CrearPacienteService._obtener_o_crear_localidad(localidad_nombre)
                localidad_id_final = localidad.id
            elif localidad_id:
                localidad = Localidad.query.get(localidad_id)
                if not localidad:
                    raise LocalidadNoEncontradaError(localidad_id=localidad_id)
                localidad_id_final = localidad_id
            
            # Crear paciente
            paciente = Paciente(
                nombre=nombre.strip(),
                apellido=apellido.strip(),
                dni=dni_limpio,
                fecha_nac=fecha_nac,
                telefono=telefono.strip() if telefono else None,
                direccion=direccion.strip() if direccion else None,
                barrio=barrio.strip() if barrio else None,
                localidad_id=localidad_id_final,
                obra_social_id=obra_social_id,
                nro_afiliado=nro_afiliado.strip() if nro_afiliado else None,
                titular=titular.strip() if titular else None,
                parentesco=parentesco.strip() if parentesco else None,
                lugar_trabajo=lugar_trabajo.strip() if lugar_trabajo else None,
            )
            
            session.add(paciente)
            session.commit()
            return paciente
            
        except (DatosInvalidosPacienteError, PacienteDuplicadoError, LocalidadNoEncontradaError):
            session.rollback()
            raise
        except Exception as exc:
            session.rollback()
            raise PacienteError(f"Error al crear paciente: {str(exc)}")
    
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
