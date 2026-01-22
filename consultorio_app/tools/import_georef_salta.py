#!/usr/bin/env python3
"""
Script para importar localidades de Salta desde API Georef de Argentina.

API Georef: https://www.argentina.gob.ar/georef/
Endpoint: https://apis.datos.gob.ar/georef/api/localidades

Uso:
    .venv\Scripts\activate
    python tools/import_georef_salta.py

Características:
    - Obtiene todos los municipios de Salta desde Georef
    - Obtiene todas las localidades de Salta desde Georef
    - Evita duplicados verificando si ya existe en BD
    - Solo guarda nombre (como define el modelo)
"""

import os
import sys
import requests
from pathlib import Path

# Agregar directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.database import db
from app.models import Localidad

# URLs de la API Georef
GEOREF_BASE_URL = "https://apis.datos.gob.ar/georef/api"

# Endpoints
MUNICIPIOS_URL = f"{GEOREF_BASE_URL}/municipios"
LOCALIDADES_URL = f"{GEOREF_BASE_URL}/localidades"


def get_municipios_salta():
    """
    Obtiene todos los municipios de Salta desde la API Georef.
    
    Returns:
        list: Lista de dicts con municipios
    """
    try:
        params = {
            'provincia': 'Salta',
            'max': 500,
            'formato': 'json'
        }
        
        print("[Georef] Obteniendo municipios de Salta...")
        response = requests.get(MUNICIPIOS_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        municipios = data.get('municipios', [])
        
        print(f"  ✓ {len(municipios)} municipios obtenidos")
        return municipios
    
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error al obtener municipios: {e}")
        return []


def get_localidades_salta():
    """
    Obtiene todas las localidades de Salta desde la API Georef.
    
    Returns:
        list: Lista de dicts con localidades
    """
    try:
        params = {
            'provincia': 'Salta',
            'max': 1000,
            'formato': 'json'
        }
        
        print("[Georef] Obteniendo localidades de Salta...")
        response = requests.get(LOCALIDADES_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        localidades = data.get('localidades', [])
        
        print(f"  ✓ {len(localidades)} localidades obtenidas")
        return localidades
    
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error al obtener localidades: {e}")
        return []


def import_georef_salta():
    """
    Importa municipios y localidades de Salta a la BD sin duplicados.
    """
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("IMPORTANDO LOCALIDADES DE SALTA DESDE GEOREF")
        print("="*70)
        
        # Obtener datos de la API
        municipios = get_municipios_salta()
        localidades = get_localidades_salta()
        
        total_added = 0
        total_skipped = 0
        total_errors = 0
        
        # Importar municipios
        print("\n[Municipios]")
        for municipio in municipios:
            try:
                nombre = municipio.get('nombre', '').strip()
                if not nombre:
                    continue
                
                existe = Localidad.query.filter_by(nombre=nombre).first()
                
                if existe:
                    print(f"  ⊘ {nombre} (ya existe)")
                    total_skipped += 1
                else:
                    localidad = Localidad(nombre=nombre)
                    db.session.add(localidad)
                    print(f"  ✓ {nombre}")
                    total_added += 1
            except Exception as e:
                print(f"  ✗ Error con {municipio.get('nombre', '?')}: {e}")
                total_errors += 1
        
        # Importar localidades (si no están ya como municipios)
        print("\n[Localidades]")
        for localidad_data in localidades:
            try:
                nombre = localidad_data.get('nombre', '').strip()
                if not nombre:
                    continue
                
                existe = Localidad.query.filter_by(nombre=nombre).first()
                
                if existe:
                    print(f"  ⊘ {nombre} (ya existe)")
                    total_skipped += 1
                else:
                    nuevo = Localidad(nombre=nombre)
                    db.session.add(nuevo)
                    print(f"  ✓ {nombre}")
                    total_added += 1
            except Exception as e:
                print(f"  ✗ Error con {localidad_data.get('nombre', '?')}: {e}")
                total_errors += 1
        
        # Guardar cambios
        try:
            db.session.commit()
            print("\n" + "="*70)
            print("✓ IMPORTACIÓN COMPLETADA")
            print(f"  Agregadas:     {total_added}")
            print(f"  Omitidas:      {total_skipped}")
            print(f"  Errores:       {total_errors}")
            print(f"  Total:         {total_added + total_skipped + total_errors}")
            print("="*70 + "\n")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ ERROR al guardar en BD: {e}\n")
            raise


if __name__ == '__main__':
    try:
        import_georef_salta()
    except KeyboardInterrupt:
        print("\n\n[CANCELADO] Importación interrumpida por el usuario\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)

