import os
from flask import Flask
from app.config import PathManager

def configure_database(app: Flask):
    """
    Configura la base de datos para la aplicación Flask.
    
    Usa PathManager para determinar la ubicación de la base de datos
    de forma dinámica (desarrollo vs PyInstaller).
    """
    # Si estamos en modo TESTING, usar SQLite en memoria para tests rápidos
    if app.config.get('TESTING') or os.environ.get('TESTING') == '1':
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        # Usar PathManager para obtener path dinámico de la base de datos
        db_path = PathManager.get_db_path()
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = False  # Cambiar a True para ver las consultas SQL
    
    return app
