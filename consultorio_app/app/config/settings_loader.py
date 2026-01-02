"""
Carga y gestiona configuración desde settings.ini

Proporciona acceso centralizado a configuración editable por el usuario
sin necesidad de modificar código fuente.

Ejemplo de uso:
    from app.config import SettingsLoader
    
    secret = SettingsLoader.get('app', 'secret_key')
    debug = SettingsLoader.get_bool('app', 'debug')
"""

import configparser
import secrets
from pathlib import Path
from .path_manager import PathManager


class SettingsLoader:
    """
    Carga y gestiona configuración desde settings.ini
    
    Si el archivo no existe, genera uno con valores por defecto seguros.
    """
    
    _config = None
    
    @classmethod
    def load(cls):
        """
        Carga la configuración desde settings.ini
        
        Returns:
            ConfigParser: Objeto de configuración cargado
        """
        if cls._config is None:
            cls._config = configparser.ConfigParser()
            config_file = PathManager.get_config_file()
            
            # Si no existe, crear config por defecto
            if not config_file.exists():
                cls._create_default_config(config_file)
            
            cls._config.read(config_file, encoding='utf-8')
        
        return cls._config
    
    @classmethod
    def _create_default_config(cls, config_file: Path):
        """
        Crea archivo de configuración por defecto.
        
        IMPORTANTE: Genera SECRET_KEY única por instalación para seguridad.
        
        Args:
            config_file: Path donde crear el archivo
        """
        config = configparser.ConfigParser()
        
        config['app'] = {
            'secret_key': secrets.token_hex(32),  # Generar clave única y segura
            'debug': 'false',
            'favicon': 'muela_icon.png',
            'auto_open_browser': 'true',
            'runner_notice': 'true'
        }
        
        config['database'] = {
            'db_name': 'consultorio.db',
            'backup_retention': '10'
        }
        
        config['logging'] = {
            'level': 'INFO',
            'max_file_size_mb': '10',
            'backup_count': '10'
        }
        
        config['scheduler'] = {
            'update_interval_minutes': '5'
        }
        
        config['whatsapp'] = {
            'phone_number_id': '',
            'access_token': '',
            'verify_token': ''
        }
        
        # Crear directorio si no existe
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
            
        print(f"[PathManager] Archivo de configuración creado: {config_file}")
    
    @classmethod
    def get(cls, section, key, fallback=None):
        """
        Obtiene un valor de configuración como string.
        
        Args:
            section: Sección del archivo INI
            key: Clave a buscar
            fallback: Valor por defecto si no existe
            
        Returns:
            str: Valor configurado o fallback
        """
        config = cls.load()
        return config.get(section, key, fallback=fallback)
    
    @classmethod
    def get_int(cls, section, key, fallback=0):
        """
        Obtiene un valor entero de configuración.
        
        Args:
            section: Sección del archivo INI
            key: Clave a buscar
            fallback: Valor por defecto si no existe
            
        Returns:
            int: Valor configurado o fallback
        """
        config = cls.load()
        return config.getint(section, key, fallback=fallback)
    
    @classmethod
    def get_bool(cls, section, key, fallback=False):
        """
        Obtiene un valor booleano de configuración.
        
        Args:
            section: Sección del archivo INI
            key: Clave a buscar
            fallback: Valor por defecto si no existe
            
        Returns:
            bool: Valor configurado o fallback
        """
        config = cls.load()
        return config.getboolean(section, key, fallback=fallback)
