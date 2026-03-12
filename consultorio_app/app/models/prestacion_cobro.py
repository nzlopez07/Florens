from sqlalchemy import Column, Integer, Float, ForeignKey, String, Date, DateTime
from sqlalchemy.orm import relationship
from app.database import db
from datetime import datetime


class PrestacionCobro(db.Model):
    __tablename__ = "prestacion_cobro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prestacion_id = Column(Integer, ForeignKey("prestaciones.id"), nullable=False)
    fecha_cobro = Column(Date, nullable=False)
    tipo_cobro = Column(String(30), nullable=False)
    # Enum: plus_consulta | plus_practica | plus_afiliado | honorario_os | otro
    monto = Column(Float, nullable=False, default=0.0)
    razon = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    prestacion = relationship("Prestacion", back_populates="cobros")

    def __str__(self):
        return f"{self.tipo_cobro} - ${self.monto} ({self.fecha_cobro.strftime('%d/%m/%Y')})"
