from sqlalchemy import Column, Integer, Float, ForeignKey, String, Date
from sqlalchemy.orm import relationship
from app.database import db

class PrestacionPractica(db.Model):
    __tablename__ = "prestacion_practica"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prestacion_id = Column(Integer, ForeignKey("prestaciones.id"), nullable=False)
    practica_id = Column(Integer, ForeignKey("practicas.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    monto_unitario = Column(Float, nullable=True)
    observaciones = Column(String, nullable=True)
    
    # NUEVOS CAMPOS IPSS
    tipo_concepto = Column(String(20), nullable=False, default='acto')
    estado_item = Column(String(20), nullable=False, default='pendiente')
    monto_autorizado = Column(Float, nullable=True)
    fecha_realizacion_item = Column(Date, nullable=True)
    fecha_anulacion = Column(Date, nullable=True)
    razon_anulacion = Column(String, nullable=True)

    prestacion = relationship("Prestacion", back_populates="practicas_assoc")
    practica = relationship("Practica", back_populates="prestaciones_assoc")
