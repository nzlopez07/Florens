"""
Módulo de configuración de Florens.

Gestiona rutas dinámicas y configuración externa para permitir
ejecución tanto en desarrollo como empaquetado con PyInstaller.
"""

from .path_manager import PathManager
from .settings_loader import SettingsLoader

__all__ = ['PathManager', 'SettingsLoader']
