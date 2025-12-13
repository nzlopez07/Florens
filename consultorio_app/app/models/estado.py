from sqlalchemy import Column, Integer, String
from app.database import db

class Estado(db.Model):
    __tablename__ = 'estados'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
