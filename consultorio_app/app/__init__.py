import os
from flask import Flask, request, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager
from flasgger import Flasgger
from flask_login import current_user
from app.config import PathManager, SettingsLoader
from app.database import db
from app.database.config import configure_database
from app.database.session import DatabaseSession
from app.logging_config import configure_logging


def get_version():
    """
    Lee la versión desde version.txt
    
    Returns:
        str: Versión de la aplicación (ej: "1.0.0")
    """
    try:
        version_file = PathManager.get_version_file()
        if version_file.exists():
            return version_file.read_text(encoding='utf-8').strip()
    except Exception:
        pass
    return '1.0.0-dev'


def create_app():
    app = Flask(__name__)
    
    # Configurar logging ANTES que nada
    configure_logging(app)
    
    # Log de inicio
    app.logger.info(f"Iniciando Florens v{get_version()}")
    app.logger.info(f"Base dir: {PathManager.get_base_dir()}")
    app.logger.info(f"Data dir: {PathManager.get_data_dir()}")
    
    # Configurar CORS para permitir peticiones desde Swagger
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configurar secret key desde settings.ini
    secret_key = SettingsLoader.get('app', 'secret_key', 'dev-secret-key-change-in-production')
    app.config['SECRET_KEY'] = secret_key
    
    # Configurar versión (disponible en templates)
    app.config['VERSION'] = get_version()
    # Configurar favicon desde settings.ini (archivo en app/media)
    app.config['FAVICON'] = SettingsLoader.get('app', 'favicon', 'muela_icon.png')
    # Aviso visual para usuarios (no cerrar mientras está abierto)
    app.config['SHOW_RUNNER_NOTICE'] = SettingsLoader.get_bool(
        'app', 'runner_notice', fallback=PathManager.is_frozen()
    )
    
    # Configurar la base de datos
    configure_database(app)
    
    # Inicializar la base de datos
    db.init_app(app)
    # Registrar singleton para sesiones
    DatabaseSession.get_instance(app)
    
    # Configurar Flask-Login (permite deshabilitarlo para tests con FLASK_LOGIN_DISABLED=1)
    if os.environ.get('FLASK_LOGIN_DISABLED') == '1':
        app.config['LOGIN_DISABLED'] = True

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Ruta para redireccionar si no está autenticado
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))

    @app.before_request
    def proteger_documentacion_swagger():
        # Permitir bypass en entornos de test si FLASK_LOGIN_DISABLED=1
        if app.config.get('LOGIN_DISABLED'):
            return None
        # Proteger /api/docs y /apispec.json con login
        if request.path.startswith('/api/docs') or request.path.startswith('/apispec'):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login', next=request.url))
    
    # Configurar Flasgger para documentación Swagger/OpenAPI
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: rule.rule.startswith('/api/'),
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }
    
    flasgger = Flasgger(
        app=app,
        config=swagger_config,
        template={
            "swagger": "2.0",
            "info": {
                "title": "API - Sistema de Gestión Odontológico",
                "description": "Documentación interactiva de endpoints disponibles. Los endpoints /api/* retornan JSON para integración con herramientas externas.",
                "version": "1.0.0",
                "contact": {
                    "name": "Soporte"
                }
            },
            "host": "localhost:5000",
            "basePath": "/",
            "schemes": ["http"],
        }
    )
    
    # Registrar custom Jinja2 filters
    @app.template_filter('empty_fallback')
    def empty_fallback(value, default='No registrado'):
        """
        Convierte valores vacíos o la cadena 'None' a un valor por defecto.
        Útil para manejar campos NULL de base de datos o strings 'None' accidentales.
        """
        if value is None or value == '' or str(value).strip() == 'None':
            return default
        return value
    
    # Inyectar variables globales en todos los templates
    @app.context_processor
    def inject_globals():
        return {
            'version': app.config['VERSION'],
            'favicon': app.config['FAVICON'],
            'show_runner_notice': app.config['SHOW_RUNNER_NOTICE'],
            'is_frozen': PathManager.is_frozen(),
        }
    
    # Registrar blueprints (rutas)
    from app.routes import main_bp
    from app.routes.webhooks import webhooks_bp
    from app.routes.admin import admin_bp
    from app.routes.finanzas import finanzas_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(finanzas_bp)
    
    # Registrar tareas periódicas (scheduler)
    # Registrar tareas periódicas (scheduler) salvo en modo testing
    if not app.config.get('TESTING') and os.environ.get('DISABLE_SCHEDULER') != '1':
        from app.scheduler import register_background_tasks
        register_background_tasks(app)
    else:
        app.logger.info("Scheduler deshabilitado en modo testing")
    
    return app