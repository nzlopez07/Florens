import os
from flask import Flask
from flask_cors import CORS
from flasgger import Flasgger
from app.database import db
from app.database.config import configure_database
from app.database.session import DatabaseSession

def create_app():
    app = Flask(__name__)
    
    # Configurar CORS para permitir peticiones desde Swagger
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configurar secret key para sesiones y CSRF
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Configurar la base de datos
    configure_database(app)
    
    # Inicializar la base de datos
    db.init_app(app)
    # Registrar singleton para sesiones
    DatabaseSession.get_instance(app)
    
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
    
    # Registrar blueprints (rutas)
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app