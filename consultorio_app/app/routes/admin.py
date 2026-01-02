"""
Rutas exclusivas para el rol ADMIN.
"""

from flask import Blueprint, render_template, abort, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
import os
import logging
from datetime import datetime
from app.config import PathManager
from app.models import Usuario, Paciente, Turno, Prestacion
from app.database import db
from sqlalchemy import text
from app.services.testing.run_tests_service import RunTestsService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorador para requerir rol ADMIN."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Permitir bypass en modo testing cuando LOGIN_DISABLED está activo
        if current_app.config.get('LOGIN_DISABLED'):
            return f(*args, **kwargs)
        if not current_user.is_authenticated or not current_user.tiene_acceso_admin():
            logger.warning(f"Acceso denegado a {request.path} - usuario: {current_user.username if current_user.is_authenticated else 'anónimo'}")
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal de administración."""
    
    # Estadísticas de BD
    stats = {
        'usuarios': Usuario.query.count(),
        'pacientes': Paciente.query.count(),
        'turnos': Turno.query.count(),
        'prestaciones': Prestacion.query.count(),
    }
    
    # Información de la base de datos (usar PathManager para ruta correcta)
    db_path = PathManager.get_db_path()
    db_info = {
        'ruta': str(db_path),
        'existe': db_path.exists(),
        'tamano': None,
        'ultima_modificacion': None
    }
    
    if db_info['existe']:
        db_info['tamano'] = db_path.stat().st_size
        db_info['ultima_modificacion'] = datetime.fromtimestamp(
            db_path.stat().st_mtime
        ).strftime('%Y-%m-%d %H:%M:%S')
    
    # Leer últimas líneas del log (usar PathManager)
    log_lines = []
    log_file = PathManager.get_logs_dir() / 'app.log'
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()[-50:]  # Últimas 50 líneas
                log_lines.reverse()  # Más recientes primero
        except Exception as e:
            log_lines = [f"Error leyendo log: {str(e)}"]
    else:
        log_lines = ["Archivo de log no encontrado"]
    
    # Usuarios del sistema
    usuarios = Usuario.query.order_by(Usuario.ultimo_login.desc()).all()
    
    # Información de backups (usar PathManager)
    backups = []
    backup_dir = PathManager.get_backups_dir()
    if backup_dir.exists():
        backup_files = sorted(backup_dir.glob('*.db'), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
        for filepath in backup_files:
            backups.append({
                'nombre': filepath.name,
                'tamano': filepath.stat().st_size,
                'fecha': datetime.fromtimestamp(
                    filepath.stat().st_mtime
                ).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        db_info=db_info,
        log_lines=log_lines,
        usuarios=usuarios,
        backups=backups
    )


@admin_bp.route('/run-tests', methods=['POST'])
@login_required
@admin_required
def run_tests():
    """Dispara la ejecución de todos los tests y registra salida en logs.

    Retorna un pequeño JSON para confirmar el inicio.
    """
    RunTestsService.ejecutar_todos()
    flash('Ejecución de tests iniciada. Revisa los logs para ver el progreso.', 'info')
    # Permitir consumo HTMX/JS o redirigir al dashboard
    if request.headers.get('Accept') == 'application/json':
        return jsonify({"status": "started"})
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/logs')
@login_required
@admin_required
def ver_logs():
    """
    Ver logs del sistema con filtros.
    
    Query params:
        - log_type: app, whatsapp, security, errors (default: app)
        - level: DEBUG, INFO, WARNING, ERROR (default: todos)
        - lines: número de líneas a mostrar (default: 200)
        - search: búsqueda de texto
    """
    log_type = request.args.get('log_type', 'app')
    level_filter = request.args.get('level', '')
    lines_count = int(request.args.get('lines', 200))
    search_term = request.args.get('search', '')
    
    # Mapeo de tipos de log a archivos
    logs_dir = PathManager.get_logs_dir()
    log_files = {
        'app': logs_dir / 'app.log',
        'whatsapp': logs_dir / 'whatsapp.log',
        'security': logs_dir / 'security.log',
        'errors': logs_dir / 'errors.log'
    }
    
    log_file = log_files.get(log_type, logs_dir / 'app.log')
    log_lines = []
    file_info = {
        'existe': False,
        'tamano': 0,
        'ultima_modificacion': None
    }
    
    if log_file.exists():
        file_info['existe'] = True
        file_info['tamano'] = log_file.stat().st_size
        file_info['ultima_modificacion'] = datetime.fromtimestamp(
            log_file.stat().st_mtime
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
                # Filtrar por nivel si se especificó
                if level_filter:
                    all_lines = [line for line in all_lines if level_filter in line]
                
                # Filtrar por término de búsqueda
                if search_term:
                    all_lines = [line for line in all_lines if search_term.lower() in line.lower()]
                
                # Tomar últimas N líneas
                log_lines = all_lines[-lines_count:]
                log_lines.reverse()  # Más recientes primero
                
        except Exception as e:
            log_lines = [f"Error leyendo log: {str(e)}"]
            logger.error(f"Error leyendo {log_file}: {e}")
    else:
        log_lines = [f"Archivo de log no encontrado: {log_file}"]
    
    return render_template(
        'admin/logs.html',
        log_lines=log_lines,
        log_type=log_type,
        level_filter=level_filter,
        lines_count=lines_count,
        search_term=search_term,
        file_info=file_info,
        log_types=['app', 'whatsapp', 'security', 'errors'],
        log_levels=['DEBUG', 'INFO', 'WARNING', 'ERROR']
    )


@admin_bp.route('/logs/download/<log_type>')
@login_required
@admin_required
def download_log(log_type):
    """Descargar archivo de log completo."""
    from flask import send_file
    
    logs_dir = PathManager.get_logs_dir()
    log_files = {
        'app': logs_dir / 'app.log',
        'whatsapp': logs_dir / 'whatsapp.log',
        'security': logs_dir / 'security.log',
        'errors': logs_dir / 'errors.log'
    }
    
    log_file = log_files.get(log_type)
    
    if not log_file or not log_file.exists():
        abort(404)
    
    logger.info(f"Descargando log: {log_type} por usuario {current_user.username}")
    
    return send_file(
        str(log_file),
        as_attachment=True,
        download_name=f"{log_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
