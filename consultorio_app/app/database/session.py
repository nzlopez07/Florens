"""Singleton para exponer la sesión de base de datos.

Esta capa permite inyectar la sesión (db.session) donde se necesite sin
recrear ni reinstanciar el objeto de SQLAlchemy.
"""
from __future__ import annotations
from typing import Optional
from flask import Flask
from . import db


class DatabaseSession:
    _instance: Optional["DatabaseSession"] = None

    def __init__(self, app: Optional[Flask] = None) -> None:
        # Forzar el uso de get_instance para mantener una sola instancia
        if DatabaseSession._instance is not None:
            raise RuntimeError("Use DatabaseSession.get_instance() en lugar de instanciar directamente")
        # Si se pasa app y aún no se registró la extensión, inicializarla; de lo contrario, reutilizarla.
        if app is not None:
            # Flask-SQLAlchemy guarda su extensión en app.extensions['sqlalchemy']
            already_registered = getattr(app, "extensions", {}).get("sqlalchemy") is not None
            if not already_registered:
                db.init_app(app)
        self._db = db

    @classmethod
    def get_instance(cls, app: Optional[Flask] = None) -> "DatabaseSession":
        if cls._instance is None:
            cls._instance = cls(app)
        return cls._instance

    @property
    def session(self):
        """Retorna la sesión activa de SQLAlchemy (scoped_session en Flask)."""
        return self._db.session

    @property
    def engine(self):
        return self._db.engine

    @property
    def metadata(self):
        return self._db.metadata
