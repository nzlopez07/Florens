import os
import shutil
from datetime import datetime
from app.config import PathManager
from app.database import db
from app.database.session import DatabaseSession
from flask import current_app

def init_database():
    """
    Inicializa la base de datos creando todas las tablas
    """
    with current_app.app_context():
        db.create_all()
        print("✅ Base de datos inicializada correctamente")

def drop_database():
    """
    Elimina todas las tablas de la base de datos
    """
    with current_app.app_context():
        db.drop_all()
        print("🗑️ Base de datos eliminada")

def reset_database():
    """
    Reinicia la base de datos (elimina y crea nuevamente)
    """
    drop_database()
    init_database()
    print("🔄 Base de datos reiniciada")

def get_session():
    """
    Obtiene la sesión actual de la base de datos
    """
    return DatabaseSession.get_instance().session

def backup_database():
    """
    Crea una copia de respaldo de la base de datos en data/backups/
    
    Usa PathManager para determinar ubicación dinámica de backups.
    
    Returns:
        str: Nombre del archivo de backup creado, o None si falla
    """
    backup_dir = PathManager.get_backups_dir()
    
    # Nombre del archivo de backup con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"consultorio_{timestamp}.db"
    
    # Rutas de origen y destino
    source_db = PathManager.get_db_path()
    backup_db = backup_dir / backup_filename
    
    # Crear el backup
    if source_db.exists():
        shutil.copy2(source_db, backup_db)
        print(f"💾 Backup creado: {backup_filename}")
        return backup_filename
    else:
        print("⚠️ No se encontró la base de datos para respaldar")
        return None

def restore_database(backup_filename):
    """.
    
    Args:
        backup_filename: Nombre del archivo de backup (sin path completo)
        
    Returns:
        bool: True si la restauración fue exitosa, False en caso contrario
    """
    backup_dir = PathManager.get_backups_dir()
    backup_path = backup_dir / backup_filename
    target_db = PathManager.get_db_path()
    
    if backup_path.exists():
        shutil.copy2(backup_path, target_db)
        print(f"🔄 Base de datos restaurada desde: {backup_filename}")
        return True
    else:
        print(f"⚠️ No se encontró el archivo de backup: {backup_filename}")
        return False


def list_backups():
    """
    Lista todos los archivos de backup disponibles.
    
    Returns:
        list: Lista de nombres de archivos de backup, ordenados por más reciente primero
    """
    backup_dir = PathManager.get_backups_dir()
    
    if backup_dir.exists():
        backups = [f.name for f in backup_dir.iterdir() if f.suffix == '.db']
        backups = [f for f in os.listdir(backup_path) if f.endswith('.db')]
        backups.sort(reverse=True)  # Más recientes primero
        return backups
    else:
        return []
