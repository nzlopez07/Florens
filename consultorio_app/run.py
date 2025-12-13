#!/usr/bin/env python3
"""
Punto de entrada principal para el Sistema de Gestión de Consultorio Odontológico
Ejecuta el servidor web Flask para la aplicación.
"""

import os
import sys
from app import create_app
from app.database import db
from app.models import *  # Importar todos los modelos para que SQLAlchemy los reconozca


def init_default_data():
    """Inicializar datos por defecto en la BD (estados, localidades, obras sociales)."""
    # Estados predefinidos para turnos
    estados_predefinidos = ['Pendiente', 'Confirmado', 'Atendido', 'NoAtendido', 'Cancelado']
    for nombre in estados_predefinidos:
        if not Estado.query.filter_by(nombre=nombre).first():
            estado = Estado(nombre=nombre)
            db.session.add(estado)
    
    # Localidades por defecto
    localidades_predefinidas = ['La Plata', 'Tolosa', 'Villa Elisa', 'Gonnet', 'Ringuelet', 'Los Hornos']
    for nombre in localidades_predefinidas:
        if not Localidad.query.filter_by(nombre=nombre).first():
            localidad = Localidad(nombre=nombre)
            db.session.add(localidad)
    
    # Obras sociales por defecto
    obras_sociales_predefinidas = [
        'OSDE', 'Medife', 'Afianzadora Salud', 'Swiss Medical', 
        'Galeno', 'IPAM', 'Farmacia del Dr. Surtidor', 'Particular'
    ]
    for nombre in obras_sociales_predefinidas:
        if not ObraSocial.query.filter_by(nombre=nombre).first():
            obra = ObraSocial(nombre=nombre)
            db.session.add(obra)
    
    db.session.commit()
    print("✅ Datos por defecto inicializados")


def main():
    app = create_app()

    with app.app_context():
        # Verificar si la BD existe y tiene esquema desactualizado
        # Si es desarrollo, recrear tablas desde cero
        if os.environ.get('FLASK_RESET_DB'):
            print("🔄 Eliminando y recreando base de datos...")
            db.drop_all()
        
        db.create_all()
        print("✅ Base de datos verificada")
        
        # Inicializar datos por defecto
        init_default_data()
    
    # Configuración del servidor
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🌐 Iniciando servidor en http://{host}:{port}")
    print("📋 Para ver ayuda: python help.py")
    print("⚡ Para verificación rápida: python quick_start.py")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()