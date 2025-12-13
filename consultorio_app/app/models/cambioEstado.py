from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import db

class CambioEstado(db.Model):
    __tablename__ = 'cambios_estado'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    turno_id = Column(Integer, ForeignKey('turnos.id'), nullable=False)
    estado_anterior = Column(String, nullable=True)  # Estado anterior (puede ser None)
    estado_nuevo = Column(String, nullable=False)     # Estado actual
    
    fecha_cambio = Column(DateTime, default=datetime.now, nullable=False)
    motivo = Column(String, nullable=True)  # Motivo del cambio

    turno = relationship("Turno", back_populates="cambios_estado")
    
    def __str__(self):
        return f"{self.estado_anterior} → {self.estado_nuevo} ({self.fecha_cambio.strftime('%d/%m/%Y %H:%M')})"
