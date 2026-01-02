"""
Gestión centralizada de rutas para desarrollo y producción (PyInstaller).

REGLA: Todas las rutas dinámicas (data, logs, config) DEBEN usar PathManager.

Ejemplo de uso:
    from app.config import PathManager
    
    db_path = PathManager.get_db_path()
    logs_dir = PathManager.get_logs_dir()
"""

import os
import sys
from pathlib import Path


class PathManager:
    """
    Gestiona rutas de forma transparente para desarrollo y PyInstaller.
    
    Detecta automáticamente si está ejecutándose:
    - Desde código fuente (desarrollo): usa rutas relativas desde run.py
    - Desde ejecutable PyInstaller (producción): usa rutas relativas desde .exe
    """
    
    _base_dir = None
    
    @classmethod
    def get_base_dir(cls) -> Path:
        """
        Obtiene el directorio base de la aplicación.
        
        Returns:
            Path: Directorio base (donde está el .exe o run.py)
        """
        if cls._base_dir is None:
            if getattr(sys, 'frozen', False):
                # Ejecutando desde PyInstaller
                # sys.executable apunta al .exe
                cls._base_dir = Path(sys.executable).parent
            else:
                # Ejecutando desde código fuente
                # __file__ está en app/config/path_manager.py
                # Subimos 3 niveles: config -> app -> consultorio_app
                cls._base_dir = Path(__file__).parent.parent.parent
        
        return cls._base_dir
    
    @classmethod
    def get_data_dir(cls) -> Path:
        """
        Directorio para base de datos y backups.
        Se crea automáticamente si no existe.
        
        Returns:
            Path: Ruta absoluta a data/
        """
        data_dir = cls.get_base_dir() / 'data'
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    @classmethod
    def get_logs_dir(cls) -> Path:
        """
        Directorio para logs.
        Se crea automáticamente si no existe.
        
        Returns:
            Path: Ruta absoluta a logs/
        """
        logs_dir = cls.get_base_dir() / 'logs'
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
    
    @classmethod
    def get_config_dir(cls) -> Path:
        """
        Directorio para configuración.
        Se crea automáticamente si no existe.
        
        Returns:
            Path: Ruta absoluta a config/
        """
        config_dir = cls.get_base_dir() / 'config'
        config_dir.mkdir(exist_ok=True)
        return config_dir
    
    @classmethod
    def get_backups_dir(cls) -> Path:
        """
        Directorio para backups de base de datos.
        Se crea automáticamente si no existe.
        
        Returns:
            Path: Ruta absoluta a data/backups/
        """
        backups_dir = cls.get_data_dir() / 'backups'
        backups_dir.mkdir(exist_ok=True)
        return backups_dir
    
    @classmethod
    def get_db_path(cls) -> Path:
        """
        Path completo de la base de datos principal.
        
        Returns:
            Path: Ruta absoluta a data/consultorio.db
        """
        return cls.get_data_dir() / 'consultorio.db'
    
    @classmethod
    def get_config_file(cls) -> Path:
        """
        Path del archivo de configuración settings.ini
        
        Returns:
            Path: Ruta absoluta a config/settings.ini
        """
        return cls.get_config_dir() / 'settings.ini'
    
    @classmethod
    def is_frozen(cls) -> bool:
        """
        Retorna True si está ejecutándose desde PyInstaller.
        
        Útil para debugging y comportamiento condicional.
        
        Returns:
            bool: True si es ejecutable, False si es código fuente
        """
        return getattr(sys, 'frozen', False)
    
    @classmethod
    def get_version_file(cls) -> Path:
        """
        Path del archivo de versión.
        
        Returns:
            Path: Ruta absoluta a version.txt
        """
        return cls.get_base_dir() / 'version.txt'
    
    @classmethod
    def get_app_dir(cls) -> Path:
        """
        Path del directorio app/ (código fuente).
        Útil para acceder a templates, media, etc.
        
        Returns:
            Path: Ruta absoluta al directorio app/
        """
        if cls.is_frozen():
            # En PyInstaller, los recursos están en sys._MEIPASS
            return Path(sys._MEIPASS) / 'app'
        else:
            # En desarrollo, subimos desde config/
            return Path(__file__).parent.parent
