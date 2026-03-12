from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import db
from datetime import datetime


class PrestacionAudit(db.Model):
    __tablename__ = "prestacion_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prestacion_id = Column(Integer, ForeignKey("prestaciones.id"), nullable=False)
    campo = Column(String(50), nullable=False)
    valor_anterior = Column(Text, nullable=True)
    valor_nuevo = Column(Text, nullable=True)
    fecha_cambio = Column(DateTime, nullable=False, default=datetime.utcnow)
    razon = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    prestacion = relationship("Prestacion", back_populates="audits")

    def __str__(self):
        return f"{self.campo}: {self.valor_anterior} → {self.valor_nuevo}"
