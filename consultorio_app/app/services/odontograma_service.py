from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy import func
from app.database.session import DatabaseSession
from app.models import Odontograma, OdontogramaCara, Paciente, Prestacion


class OdontogramaService:
    """Servicio para gestionar odontogramas versionados por paciente."""

    RETENCION_MAX_VERSIONES = 20  # configurable; se puede bajar a 5 si la doctora lo requiere

    @staticmethod
    def _obtener_sesion():
        return DatabaseSession.get_instance().session

    @staticmethod
    def _obtener_versiones(paciente_id: int, limite: int = 20) -> List[Odontograma]:
        session = OdontogramaService._obtener_sesion()
        return (
            session.query(Odontograma)
            .filter(Odontograma.paciente_id == paciente_id)
            .order_by(Odontograma.version_seq.desc())
            .limit(limite)
            .all()
        )

    @staticmethod
    def _aplicar_retencion_versiones(session, paciente_id: int):
        ids_ordenados = [row[0] for row in session.query(Odontograma.id)
                         .filter(Odontograma.paciente_id == paciente_id)
                         .order_by(Odontograma.version_seq.desc())
                         .all()]
        if len(ids_ordenados) > OdontogramaService.RETENCION_MAX_VERSIONES:
            ids_a_eliminar = ids_ordenados[OdontogramaService.RETENCION_MAX_VERSIONES:]
            if ids_a_eliminar:
                antiguos = session.query(Odontograma).filter(Odontograma.id.in_(ids_a_eliminar)).all()
                for od in antiguos:
                    session.delete(od)

    @staticmethod
    def _ultima_prestacion_timestamp(paciente_id: int) -> Optional[datetime]:
        session = OdontogramaService._obtener_sesion()
        return session.query(func.max(Prestacion.fecha)).filter(Prestacion.paciente_id == paciente_id).scalar()

    @staticmethod
    def _marcar_solo_un_actual(session, paciente_id: int, odontograma_actual_id: int):
        session.query(Odontograma).filter(
            Odontograma.paciente_id == paciente_id,
            Odontograma.id != odontograma_actual_id,
        ).update({Odontograma.es_actual: False}, synchronize_session=False)

    @staticmethod
    def obtener_o_crear_actual(paciente_id: int) -> Tuple[Odontograma, List[Odontograma], bool, Optional[datetime]]:
        """Obtiene el odontograma actual (es_actual) o lo crea vacío si no existe.
        Retorna (odontograma, versiones, desactualizado, ultima_prestacion).
        """
        session = OdontogramaService._obtener_sesion()

        paciente = session.get(Paciente, paciente_id)
        if not paciente:
            raise ValueError("Paciente no encontrado")

        odontograma = (
            session.query(Odontograma)
            .filter_by(paciente_id=paciente_id, es_actual=True)
            .order_by(Odontograma.version_seq.desc())
            .first()
        )

        if not odontograma:
            max_version = (
                session.query(func.max(Odontograma.version_seq))
                .filter(Odontograma.paciente_id == paciente_id)
                .scalar()
            ) or 0

            odontograma = Odontograma(
                paciente_id=paciente_id,
                version_seq=max_version + 1,
                es_actual=True,
                nota_general=None,
                ultima_prestacion_registrada_en=OdontogramaService._ultima_prestacion_timestamp(paciente_id),
            )
            session.add(odontograma)
            session.flush()
            OdontogramaService._marcar_solo_un_actual(session, paciente_id, odontograma.id)
            session.commit()

        versiones = OdontogramaService._obtener_versiones(paciente_id, limite=OdontogramaService.RETENCION_MAX_VERSIONES)
        ultima_prestacion = OdontogramaService._ultima_prestacion_timestamp(paciente_id)
        desactualizado = False
        # Comparar con creado_en para detectar prestaciones posteriores a la creación del odontograma
        if ultima_prestacion and odontograma.creado_en and ultima_prestacion > odontograma.creado_en:
            desactualizado = True

        return odontograma, versiones, desactualizado, ultima_prestacion

    @staticmethod
    def obtener_version(paciente_id: int, odontograma_id: int) -> Tuple[Optional[Odontograma], List[Odontograma], bool, Optional[datetime]]:
        session = OdontogramaService._obtener_sesion()
        odontograma = session.get(Odontograma, odontograma_id)
        if not odontograma or odontograma.paciente_id != paciente_id:
            return None, [], False, None

        versiones = OdontogramaService._obtener_versiones(paciente_id, limite=OdontogramaService.RETENCION_MAX_VERSIONES)
        ultima_prestacion = OdontogramaService._ultima_prestacion_timestamp(paciente_id)
        desactualizado = False
        # Comparar con creado_en para detectar prestaciones posteriores a la creación del odontograma
        if ultima_prestacion and odontograma.creado_en and ultima_prestacion > odontograma.creado_en:
            desactualizado = True

        return odontograma, versiones, desactualizado, ultima_prestacion

    @staticmethod
    def _serializar_odontograma(odontograma: Odontograma) -> dict:
        return {
            "id": odontograma.id,
            "version_seq": odontograma.version_seq,
            "es_actual": odontograma.es_actual,
            "nota_general": odontograma.nota_general,
            "paciente_id": odontograma.paciente_id,
            "creado_en": odontograma.creado_en.isoformat() if odontograma.creado_en else None,
            "actualizado_en": odontograma.actualizado_en.isoformat() if odontograma.actualizado_en else None,
            "ultima_prestacion_registrada_en": odontograma.ultima_prestacion_registrada_en.isoformat() if odontograma.ultima_prestacion_registrada_en else None,
            "caras": [
                {
                    "id": c.id,
                    "diente": c.diente,
                    "cara": c.cara,
                    "marca_codigo": c.marca_codigo,
                    "marca_texto": c.marca_texto,
                    "comentario": c.comentario,
                }
                for c in odontograma.caras
            ],
        }

    @staticmethod
    def crear_version_desde(paciente_id: int, cambios_caras: List[dict], nota_general: Optional[str] = None,
                             base_odontograma_id: Optional[int] = None) -> Tuple[Odontograma, List[Odontograma]]:
        """Crea una nueva versión a partir de la versión base (por defecto la actual) aplicando cambios de caras.
        Retorna (nuevo_odontograma, versiones_actualizadas).
        """
        session = OdontogramaService._obtener_sesion()

        paciente = session.get(Paciente, paciente_id)
        if not paciente:
            raise ValueError("Paciente no encontrado")

        base_odontograma = None
        if base_odontograma_id:
            base_odontograma = session.get(Odontograma, base_odontograma_id)
            if not base_odontograma or base_odontograma.paciente_id != paciente_id:
                raise ValueError("Odontograma base no encontrado para este paciente")
        else:
            base_odontograma = (
                session.query(Odontograma)
                .filter_by(paciente_id=paciente_id, es_actual=True)
                .order_by(Odontograma.version_seq.desc())
                .first()
            )

        if not base_odontograma:
            base_odontograma, _, _, _ = OdontogramaService.obtener_o_crear_actual(paciente_id)

        max_version = (
            session.query(func.max(Odontograma.version_seq))
            .filter(Odontograma.paciente_id == paciente_id)
            .scalar()
        ) or 0

        nuevo_odontograma = Odontograma(
            paciente_id=paciente_id,
            version_seq=max_version + 1,
            es_actual=True,
            nota_general=nota_general,
            ultima_prestacion_registrada_en=datetime.now(),
            creado_en=datetime.now(),
            actualizado_en=datetime.now(),
        )
        session.add(nuevo_odontograma)
        session.flush()

        base_caras = session.query(OdontogramaCara).filter_by(odontograma_id=base_odontograma.id).all()
        nuevo_caras_map = {}
        for cara in base_caras:
            clon = OdontogramaCara(
                odontograma_id=nuevo_odontograma.id,
                diente=cara.diente,
                cara=cara.cara,
                marca_codigo=cara.marca_codigo,
                marca_texto=cara.marca_texto,
                comentario=cara.comentario,
            )
            session.add(clon)
            session.flush()
            nuevo_caras_map[(clon.diente, clon.cara)] = clon

        for cambio in cambios_caras or []:
            diente = (cambio.get('diente') or '').strip()
            cara = (cambio.get('cara') or '').strip()
            if not diente or not cara:
                continue

            borrar = bool(cambio.get('borrar'))
            marca_codigo = cambio.get('marca_codigo')
            marca_texto = cambio.get('marca_texto')
            comentario = cambio.get('comentario')

            clave = (diente, cara)
            existente = nuevo_caras_map.get(clave)

            if borrar:
                if existente:
                    session.delete(existente)
                    nuevo_caras_map.pop(clave, None)
                continue

            if not existente:
                existente = OdontogramaCara(
                    odontograma_id=nuevo_odontograma.id,
                    diente=diente,
                    cara=cara,
                )
                session.add(existente)
                session.flush()
                nuevo_caras_map[clave] = existente

            existente.marca_codigo = marca_codigo
            existente.marca_texto = marca_texto
            existente.comentario = comentario

        OdontogramaService._marcar_solo_un_actual(session, paciente_id, nuevo_odontograma.id)
        OdontogramaService._aplicar_retencion_versiones(session, paciente_id)
        session.commit()

        versiones = OdontogramaService._obtener_versiones(paciente_id, limite=OdontogramaService.RETENCION_MAX_VERSIONES)
        return nuevo_odontograma, versiones
