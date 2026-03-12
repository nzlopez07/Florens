"""
Servicio para actualizar prestaciones en estado borrador.
Permite corregir cantidades, prácticas y montos antes de autorizar.
"""

from datetime import datetime
from typing import Dict, Any
from app.database.session import DatabaseSession
from app.models import Prestacion, PrestacionPractica, Practica, Paciente
from app.services.prestacion.crear_prestacion_service import CrearPrestacionService
from app.services.common import (
    PrestacionNoEncontradaError,
    EstadoPrestacionInvalidoError,
    PacienteNoEncontradoError,
    PracticaNoEncontradaError,
    DatosInvalidosError,
)


class ActualizarPrestacionService:
    """Actualiza una prestación existente en borrador."""

    @staticmethod
    def execute(prestacion_id: int, data: Dict[str, Any]) -> Prestacion:
        session = DatabaseSession.get_instance().session

        prestacion = session.query(Prestacion).filter(Prestacion.id == prestacion_id).first()
        if not prestacion:
            raise PrestacionNoEncontradaError(prestacion_id)

        if prestacion.estado != 'borrador':
            raise EstadoPrestacionInvalidoError(prestacion.estado, 'borrador')

        paciente_id = data.get('paciente_id') or prestacion.paciente_id
        paciente = session.query(Paciente).filter(Paciente.id == paciente_id).first()
        if not paciente:
            raise PacienteNoEncontradoError(paciente_id)

        descripcion = data.get('descripcion')
        if not descripcion or (isinstance(descripcion, str) and not descripcion.strip()):
            raise DatosInvalidosError('descripcion es requerida y no puede estar vacía')
        if isinstance(descripcion, str):
            descripcion = descripcion.strip()

        observaciones = data.get('observaciones')
        if observaciones and isinstance(observaciones, str):
            observaciones = observaciones.strip() or None
        else:
            observaciones = None

        descuento_porcentaje = float(data.get('descuento_porcentaje', 0))
        descuento_fijo = float(data.get('descuento_fijo', 0))
        if descuento_porcentaje < 0 or descuento_porcentaje > 100:
            raise DatosInvalidosError('descuento_porcentaje debe estar entre 0 y 100')
        if descuento_fijo < 0:
            raise DatosInvalidosError('descuento_fijo no puede ser negativo')

        practicas_ids, cantidades_por_id = CrearPrestacionService._normalize_practicas(
            data.get('practicas', [])
        )

        practicas = session.query(Practica).filter(Practica.id.in_(practicas_ids)).all()
        if len(practicas) != len(practicas_ids):
            encontradas = {p.id for p in practicas}
            no_encontradas = set(practicas_ids) - encontradas
            raise PracticaNoEncontradaError(
                f'Prácticas no encontradas: {", ".join(str(pid) for pid in no_encontradas)}'
            )

        subtotal = sum(
            (p.monto_unitario or 0) * cantidades_por_id.get(p.id, 1)
            for p in practicas
        )

        monto = subtotal * (1 - descuento_porcentaje / 100)
        monto = max(0, monto - descuento_fijo)

        prestacion.paciente_id = paciente_id
        prestacion.descripcion = descripcion
        prestacion.observaciones = observaciones
        prestacion.monto = monto
        prestacion.fecha = prestacion.fecha or datetime.now()

        prestacion.practicas_assoc.clear()
        session.flush()

        for practica in practicas:
            # Si es consulta (código 101), marcar como realizada automáticamente
            es_consulta = practica.codigo == '101'
            estado_item = 'realizado' if es_consulta else 'pendiente'
            fecha_realizacion_item = prestacion.fecha_solicitud if es_consulta else None
            
            pp = PrestacionPractica(
                prestacion_id=prestacion.id,
                practica_id=practica.id,
                cantidad=cantidades_por_id.get(practica.id, 1),
                monto_unitario=practica.monto_unitario,
                estado_item=estado_item,
                fecha_realizacion_item=fecha_realizacion_item,
            )
            session.add(pp)

        session.commit()
        return prestacion
