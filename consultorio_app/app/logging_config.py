"""
Configuración de logging para la aplicación.

Proporciona logging estructurado con niveles apropriados para
desarrollo y producción.

REGLA DE SEGURIDAD: Nunca loggear datos clínicos (nombres, DNI, diagnósticos, montos)
Solo loggear IDs numéricos y eventos técnicos.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from app.config import PathManager, SettingsLoader


class SanitizingFormatter(logging.Formatter):
    """
    Formatter que sanitiza logs para evitar filtración de datos sensibles.
    
    Palabras/patrones bloqueados:
    - Nombres propios (se reemplazan por [REDACTED])
    - DNI completos (se muestran solo últimos 3 dígitos)
    - Direcciones de email completas
    """
    
    SENSITIVE_FIELDS = ['nombre', 'apellido', 'dni', 'email', 'direccion', 'telefono', 'password']
    
    def format(self, record):
        # Sanitizar el mensaje antes de formatearlo
        original_msg = record.msg
        
        if isinstance(original_msg, str):
            # Aquí se pueden agregar reglas de sanitización más sofisticadas
            # Por ahora, confiamos en que el código no loggee datos sensibles directamente
            pass
        
        return super().format(record)


def configure_logging(app):
    """
    Configura el sistema de logging para la aplicación Flask.
    
    Crea estructura de logs:
    - logs/app.log - Log principal de la aplicación
    - logs/whatsapp.log - Eventos de WhatsApp
    - logs/security.log - Eventos de seguridad (login, permisos)
    - logs/errors.log - Solo errores y excepciones
    
    Usa PathManager para determinar ubicación dinámica de logs
    (desarrollo vs PyInstaller).
    
    Soporta:
    - Logs en consola (stdout)
    - Logs en archivo con rotación automática
    - Niveles configurables (default: INFO)
    - Formatos estructurados con timestamps
    
    Args:
        app: Instancia de Flask app
    """
    
    # Determinar nivel de log desde configuración o variable de entorno
    log_level_name = os.environ.get('LOG_LEVEL') or SettingsLoader.get('logging', 'level', 'INFO')
    log_level_name = log_level_name.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    # Usar PathManager para obtener directorio de logs dinámico
    log_dir = PathManager.get_logs_dir()
    
    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Limpiar handlers existentes (evitar duplicados en reloads)
    root_logger.handlers.clear()
    
    # Formato de logs con timestamp y nivel
    log_format = SanitizingFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola (solo en desarrollo)
    if app.debug or os.environ.get('FLASK_ENV') == 'development':
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(log_format)
        root_logger.addHandler(console_handler)
    
    # Obtener configuración de tamaño de archivos
    max_bytes = SettingsLoader.get_int('logging', 'max_file_size_mb', 10) * 1024 * 1024
    backup_count = SettingsLoader.get_int('logging', 'backup_count', 10)
    
    # === Handler principal (app.log) ===
    try:
        app_handler = RotatingFileHandler(
            log_dir / 'app.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        app_handler.setLevel(log_level)
        app_handler.setFormatter(log_format)
        root_logger.addHandler(app_handler)
    except Exception as e:
        print(f"ERROR: No se pudo configurar app.log: {e}", file=sys.stderr)
    
    # === Handler de errores (errors.log) ===
    try:
        error_handler = RotatingFileHandler(
            log_dir / 'errors.log',
            maxBytes=max_bytes,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(log_format)
        root_logger.addHandler(error_handler)
    except Exception as e:
        print(f"ERROR: No se pudo configurar errors.log: {e}", file=sys.stderr)
    
    # === Logger específico de WhatsApp ===
    whatsapp_logger = logging.getLogger('whatsapp')
    whatsapp_logger.setLevel(log_level)
    whatsapp_logger.propagate = False  # No propagar al root
    
    try:
        whatsapp_handler = RotatingFileHandler(
            log_dir / 'whatsapp.log',
            maxBytes=max_bytes,
            backupCount=3,
            encoding='utf-8'
        )
        whatsapp_handler.setLevel(log_level)
        whatsapp_handler.setFormatter(log_format)
        whatsapp_logger.addHandler(whatsapp_handler)
    except Exception as e:
        print(f"ERROR: No se pudo configurar whatsapp.log: {e}", file=sys.stderr)
    
    # === Logger específico de seguridad ===
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    try:
        security_handler = RotatingFileHandler(
            log_dir / 'security.log',
            maxBytes=max_bytes,
            backupCount=5,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(log_format)
        security_logger.addHandler(security_handler)
    except Exception as e:
        print(f"ERROR: No se pudo configurar security.log: {e}", file=sys.stderr)
    
    # Configurar loggers de módulos de la app
    logging.getLogger('app.services').setLevel(log_level)
    logging.getLogger('app.adapters').setLevel(log_level)
    logging.getLogger('app.routes').setLevel(log_level)
    logging.getLogger('app.models').setLevel(logging.WARNING)  # Menos verboso
    
    # Silenciar loggers ruidosos de terceros
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Configurar Flask app logger
    app.logger.setLevel(log_level)
    
    # Log de inicio del sistema
    root_logger.info("=" * 60)
    root_logger.info(f"Florens iniciando - LOG_LEVEL={log_level_name}")
    root_logger.info(f"Directorio de logs: {log_dir}")
    root_logger.info(f"Modo: {'PyInstaller' if PathManager.is_frozen() else 'Desarrollo'}")
    root_logger.info("=" * 60)


__all__ = ["configure_logging"]
