"""
Servicio para eliminar prestaciones en estado borrador.
Solo permite borrado físico de prestaciones que aún no fueron autorizadas.
"""

from app.database.session import DatabaseSession
from app.models import Prestacion
from app.services.common import (
    PrestacionNoEncontradaError,
    EstadoPrestacionInvalidoError,
)


class EliminarPrestacionService:
    """Elimina físicamente una prestación en estado borrador."""

    @staticmethod
    def execute(prestacion_id: int) -> None:
        """
        Elimina una prestación y todos sus registros asociados (cascade).

        Args:
            prestacion_id: ID de la prestación a eliminar.

        Raises:
            PrestacionNoEncontradaError: Si la prestación no existe.
            EstadoPrestacionInvalidoError: Si la prestación no está en borrador.
        """
        session = DatabaseSession.get_instance().session

        prestacion = session.query(Prestacion).filter(
            Prestacion.id == prestacion_id
        ).first()

        if not prestacion:
            raise PrestacionNoEncontradaError(prestacion_id)

        if prestacion.estado != 'borrador':
            raise EstadoPrestacionInvalidoError(prestacion.estado, 'eliminar')

        session.delete(prestacion)
        session.commit()
