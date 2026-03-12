from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import db
from datetime import datetime

class Prestacion(db.Model):
    __tablename__ = "prestaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    paciente = relationship("Paciente", back_populates="prestaciones")
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, nullable=False)
    observaciones = Column(String, nullable=True)
    
    # NUEVOS CAMPOS IPSS
    estado = Column(String(20), nullable=False, default='borrador')
    fecha_solicitud = Column(Date, nullable=False, default=datetime.utcnow().date)
    fecha_autorizacion = Column(Date, nullable=True)
    fecha_realizacion = Column(Date, nullable=True)
    importe_afiliado_autorizado = Column(Float, nullable=True)
    importe_coseguro_autorizado = Column(Float, nullable=True)
    importe_profesional_autorizado = Column(Float, nullable=True)
    autorizacion_adjunta_path = Column(String(255), nullable=True)
    observaciones_autorizacion = Column(String, nullable=True)
    
    # Relaciones
    turnos = relationship("Turno", back_populates="prestacion")
    practicas_assoc = relationship("PrestacionPractica", back_populates="prestacion", cascade="all, delete-orphan")
    cobros = relationship("PrestacionCobro", back_populates="prestacion", cascade="all, delete-orphan")
    audits = relationship("PrestacionAudit", back_populates="prestacion", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("fecha_realizacion IS NULL OR fecha_autorizacion IS NULL OR fecha_realizacion >= fecha_autorizacion"),
    )

    def get_codigos(self) -> list[str]:
        codigos = []
        if self.practicas_assoc:
            for pp in self.practicas_assoc:
                if pp.practica and pp.practica.codigo:
                    codigos.append(pp.practica.codigo)
        return codigos

    def get_codigo(self) -> str | None:
        codes = self.get_codigos()
        if not codes:
            return None
        return ", ".join(codes)

    def __str__(self):
        codigo_str = f" ({self.get_codigo()})" if self.get_codigo() else ""
        return f"{self.descripcion}{codigo_str} - ${self.monto} ({self.fecha.strftime('%d/%m/%Y')})"