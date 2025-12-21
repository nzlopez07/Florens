from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import db


class Odontograma(db.Model):
    __tablename__ = "odontogramas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False, index=True)
    version_seq = Column(Integer, nullable=False, default=1)  # consecutivo por paciente
    es_actual = Column(Boolean, default=True, nullable=False)
    nota_general = Column(String, nullable=True)
    ultima_prestacion_registrada_en = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=datetime.now, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.now, nullable=False)

    paciente = relationship("Paciente", back_populates="odontogramas")
    caras = relationship("OdontogramaCara", back_populates="odontograma", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('paciente_id', 'version_seq', name='uq_odontograma_paciente_version'),
    )


class OdontogramaCara(db.Model):
    __tablename__ = "odontograma_caras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    odontograma_id = Column(Integer, ForeignKey("odontogramas.id"), nullable=False, index=True)
    diente = Column(String, nullable=False)  # código FDI o Universal
    cara = Column(String, nullable=False)    # mesial, distal, oclusal/incisal, lingual/palatina, vestibular/buccal
    marca_codigo = Column(String, nullable=True)  # FK futura a catálogo
    marca_texto = Column(String, nullable=True)   # texto libre mientras no exista catálogo
    comentario = Column(String, nullable=True)

    odontograma = relationship("Odontograma", back_populates="caras")

    __table_args__ = (
        UniqueConstraint('odontograma_id', 'diente', 'cara', name='uq_cara_por_diente'),
    )
