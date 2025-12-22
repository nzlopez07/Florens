"""
Excepciones de negocio centralizadas para OdontoApp.

Las excepciones en este módulo representan violaciones de reglas de negocio,
no errores técnicos. Los services las lanzan; las routes las capturan y deciden
cómo responder (flash, JSON, etc).

Esto mantiene la lógica de negocio separada de detalles HTTP.
"""


class OdontoAppError(Exception):
    """Excepción base para todas las excepciones de negocio."""
    
    def __init__(self, mensaje: str, codigo: str = None):
        self.mensaje = mensaje
        self.codigo = codigo or self.__class__.__name__
        super().__init__(self.mensaje)


# ============================================================================
# EXCEPCIONES DE PACIENTE
# ============================================================================

class PacienteError(OdontoAppError):
    """Error relacionado con operaciones de paciente."""
    pass


class PacienteNoEncontradoError(PacienteError):
    """El paciente buscado no existe."""
    
    def __init__(self, paciente_id: int = None):
        msg = f"Paciente no encontrado" + (f" (ID: {paciente_id})" if paciente_id else "")
        super().__init__(msg, "PACIENTE_NO_ENCONTRADO")


class PacienteDuplicadoError(PacienteError):
    """Ya existe un paciente con el mismo DNI."""
    
    def __init__(self, dni: str):
        super().__init__(
            f"Ya existe un paciente con DNI {dni}",
            "PACIENTE_DUPLICADO"
        )


class DatosInvalidosPacienteError(PacienteError):
    """Los datos del paciente violan reglas de validación."""
    
    def __init__(self, campo: str, razon: str):
        super().__init__(
            f"Campo '{campo}' inválido: {razon}",
            "DATOS_INVALIDOS_PACIENTE"
        )


# ============================================================================
# EXCEPCIONES DE LOCALIDAD
# ============================================================================

class LocalidadError(OdontoAppError):
    """Error relacionado con operaciones de localidad."""
    pass


class LocalidadNoEncontradaError(LocalidadError):
    """La localidad buscada no existe."""
    
    def __init__(self, localidad_id: int = None, nombre: str = None):
        if localidad_id:
            msg = f"Localidad no encontrada (ID: {localidad_id})"
        elif nombre:
            msg = f"Localidad no encontrada: {nombre}"
        else:
            msg = "Localidad no encontrada"
        super().__init__(msg, "LOCALIDAD_NO_ENCONTRADA")


# ============================================================================
# EXCEPCIONES DE TURNO
# ============================================================================

class TurnoError(OdontoAppError):
    """Error relacionado con operaciones de turno."""
    pass


class TurnoNoEncontradoError(TurnoError):
    """El turno buscado no existe."""
    
    def __init__(self, turno_id: int):
        super().__init__(
            f"Turno no encontrado (ID: {turno_id})",
            "TURNO_NO_ENCONTRADO"
        )


class TurnoSolapamientoError(TurnoError):
    """El turno propuesto se solapa con otros existentes."""
    
    def __init__(self, detalles: list):
        msg = f"El horario se solapa con {len(detalles)} turno(s) existente(s): " + ", ".join(detalles)
        super().__init__(msg, "TURNO_SOLAPAMIENTO")


class TurnoFechaInvalidaError(TurnoError):
    """La fecha del turno no es válida."""
    
    def __init__(self, razon: str):
        super().__init__(razon, "TURNO_FECHA_INVALIDA")


class TurnoHoraInvalidaError(TurnoError):
    """La hora del turno no es válida."""
    
    def __init__(self, razon: str):
        super().__init__(razon, "TURNO_HORA_INVALIDA")


class TurnoDuracionInvalidaError(TurnoError):
    """La duración del turno no es válida."""
    
    def __init__(self, duracion: int):
        super().__init__(
            f"Duración {duracion} min inválida. Debe estar entre 5 y 480 minutos.",
            "TURNO_DURACION_INVALIDA"
        )


class TransicionEstadoInvalidaError(TurnoError):
    """No se puede cambiar de ese estado a otro."""
    
    def __init__(self, estado_actual: str, estado_nuevo: str, permitidos: list = None):
        msg = f"No se puede cambiar de '{estado_actual}' a '{estado_nuevo}'"
        if permitidos:
            msg += f". Transiciones permitidas: {', '.join(permitidos)}"
        super().__init__(msg, "TRANSICION_ESTADO_INVALIDA")


class EstadoFinalError(TurnoError):
    """El turno está en estado final y no se puede modificar."""
    
    def __init__(self, estado_actual: str):
        super().__init__(
            f"El turno está en estado '{estado_actual}' (final). No se pueden hacer cambios.",
            "ESTADO_FINAL"
        )


class TurnoYaAtendidoError(TurnoError):
    """El turno ya ha sido atendido y no puede ser modificado."""
    
    def __init__(self):
        super().__init__(
            "El turno ya fue atendido. No se puede cambiar su estado.",
            "TURNO_YA_ATENDIDO"
        )


class TurnoPendienteEliminableError(TurnoError):
    """Solo se pueden eliminar turnos Pendientes."""
    
    def __init__(self, estado_actual: str):
        super().__init__(
            f"Solo se pueden eliminar turnos Pendientes. Este está: {estado_actual}",
            "TURNO_NO_ELIMNABLE"
        )


# ============================================================================
# EXCEPCIONES DE ODONTOGRAMA
# ============================================================================

class OdontogramaError(OdontoAppError):
    """Error relacionado con operaciones de odontograma."""
    pass


class OdontogramaNoEncontradoError(OdontogramaError):
    """El odontograma buscado no existe."""
    
    def __init__(self, odontograma_id: int):
        super().__init__(
            f"Odontograma no encontrado (ID: {odontograma_id})",
            "ODONTOGRAMA_NO_ENCONTRADO"
        )


# ============================================================================
# EXCEPCIONES DE CONVERSACIÓN (WhatsApp futura)
# ============================================================================

class ConversacionError(OdontoAppError):
    """Error relacionado con operaciones de conversación."""
    pass


class MensajeInvalidoError(ConversacionError):
    """El mensaje recibido es inválido o malformado."""
    
    def __init__(self, razon: str):
        super().__init__(f"Mensaje inválido: {razon}", "MENSAJE_INVALIDO")


# ============================================================================
# EXCEPCIONES DE BASE DE DATOS
# ============================================================================

class BaseDatosError(OdontoAppError):
    """Error de persistencia en la base de datos."""
    pass


class TransactionError(BaseDatosError):
    """Error durante una transacción de base de datos."""
    
    def __init__(self, razon: str):
        super().__init__(f"Error en transacción: {razon}", "TRANSACTION_ERROR")


# ============================================================================
# EXCEPCIONES DE PRACTICA
# ============================================================================

class PracticaError(OdontoAppError):
    """Error relacionado con operaciones de práctica."""
    pass


class PracticaNoEncontradaError(PracticaError):
    """La práctica buscada no existe."""
    
    def __init__(self, practica_id: int = None, razon: str = None):
        msg = f"Práctica no encontrada" + (f" (ID: {practica_id})" if practica_id else "")
        if razon:
            msg += f": {razon}"
        super().__init__(msg, "PRACTICA_NO_ENCONTRADA")


class PracticaConDependenciasError(PracticaError):
    """No se puede eliminar la práctica porque tiene dependencias."""
    
    def __init__(self, razon: str):
        super().__init__(f"Práctica no se puede eliminar: {razon}", "PRACTICA_CON_DEPENDENCIAS")


class PracticaDuplicadaError(PracticaError):
    """Ya existe una práctica con el mismo código."""
    
    def __init__(self, codigo: str):
        super().__init__(
            f"Ya existe una práctica con código {codigo}",
            "PRACTICA_DUPLICADA"
        )


# ============================================================================
# EXCEPCIONES DE PRESTACION
# ============================================================================

class PrestacionError(OdontoAppError):
    """Error relacionado con operaciones de prestación."""
    pass


class PrestacionNoEncontradaError(PrestacionError):
    """La prestación buscada no existe."""
    
    def __init__(self, prestacion_id: int = None):
        msg = f"Prestación no encontrada" + (f" (ID: {prestacion_id})" if prestacion_id else "")
        super().__init__(msg, "PRESTACION_NO_ENCONTRADA")


# ============================================================================
# EXCEPCIONES DE TURNO (adicionales)
# ============================================================================

class EstadoTurnoInvalidoError(TurnoError):
    """El estado del turno es inválido para la operación solicitada."""
    
    def __init__(self, razon: str):
        super().__init__(f"Estado de turno inválido: {razon}", "ESTADO_TURNO_INVALIDO")


# ============================================================================
# EXCEPCIONES GENERICAS DE VALIDACION
# ============================================================================

class DatosInvalidosError(OdontoAppError):
    """Los datos proporcionados son inválidos."""
    
    def __init__(self, razon: str):
        super().__init__(f"Datos inválidos: {razon}", "DATOS_INVALIDOS")


# ============================================================================
# EXCEPCIONES DE OBRA SOCIAL
# ============================================================================

class ObraSocialError(OdontoAppError):
    """Error relacionado con operaciones de obra social."""
    pass


class ObraSocialNoEncontradaError(ObraSocialError):
    """La obra social buscada no existe."""
    
    def __init__(self, obra_social_id: int = None):
        msg = f"Obra social no encontrada" + (f" (ID: {obra_social_id})" if obra_social_id else "")
        super().__init__(msg, "OBRA_SOCIAL_NO_ENCONTRADA")
