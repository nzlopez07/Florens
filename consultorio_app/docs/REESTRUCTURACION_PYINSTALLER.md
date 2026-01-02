# 🏗️ REESTRUCTURACIÓN PARA PYINSTALLER - COMPLETADA

**Fecha:** 28 de Diciembre de 2025  
**Objetivo:** Preparar Florens para empaquetado como aplicación de escritorio

---

## ✅ CAMBIOS IMPLEMENTADOS

### 1. **Nuevo módulo de gestión de rutas** (`app/config/path_manager.py`)
- ✅ Detección automática de entorno (desarrollo vs PyInstaller)
- ✅ Rutas dinámicas para data/, logs/, config/
- ✅ Creación automática de carpetas
- ✅ Compatible con sys.frozen (PyInstaller)

### 2. **Configuración externa** (`config/settings.ini`)
- ✅ Archivo INI editable por el usuario
- ✅ SECRET_KEY única por instalación (generada automáticamente)
- ✅ Configuración de logs, backups, scheduler
- ✅ Loader centralizado (`app/config/settings_loader.py`)

### 3. **Actualización de archivos core**

#### `app/database/config.py`
- ✅ Usa `PathManager.get_db_path()` en lugar de ruta hardcodeada
- ✅ Compatible con desarrollo y PyInstaller

#### `app/logging_config.py`
- ✅ Usa `PathManager.get_logs_dir()` en lugar de `logs/`
- ✅ Lee configuración desde settings.ini
- ✅ Tamaño de archivos y backup count configurables

#### `app/database/utils.py`
- ✅ Funciones de backup/restore usan PathManager
- ✅ Backups en `data/backups/` en lugar de `instance/backups/`
- ✅ Compatible con Path objects (pathlib)

#### `app/__init__.py`
- ✅ Carga SECRET_KEY desde settings.ini
- ✅ Función `get_version()` lee version.txt
- ✅ Versión disponible en todos los templates (context processor)
- ✅ Logs de inicio mejorados con info de rutas

#### `app/templates/base.html`
- ✅ Footer con versión visible (`v{{ version }}`)

### 4. **Nuevos archivos creados**

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `path_manager.py` | `app/config/` | Gestión centralizada de rutas |
| `settings_loader.py` | `app/config/` | Carga de configuración desde INI |
| `settings.ini` | `config/` | Configuración editable externa |
| `version.txt` | raíz | Versión de la aplicación |
| `LEEME.txt` | raíz | Manual de usuario |
| `Florens.spec` | raíz | Archivo de configuración de PyInstaller |

### 5. **Actualización de .gitignore**
- ✅ Excluye `data/` (datos locales)
- ✅ Excluye `config/settings.ini` (configuración local)
- ✅ Excluye `build/`, `dist/`, `*.spec` (PyInstaller)
- ✅ Mantiene exclusión de logs/

---

## 📁 NUEVA ESTRUCTURA DE CARPETAS

### En desarrollo (ahora):
```
consultorio_app/
├── app/                    # Código fuente
│   ├── config/            # ✅ NUEVO
│   │   ├── path_manager.py
│   │   └── settings_loader.py
│   ├── database/
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── templates/
├── config/                # ✅ NUEVO (externa)
│   └── settings.ini
├── data/                  # ✅ NUEVO (auto-creada)
│   ├── consultorio.db
│   └── backups/
├── logs/                  # (auto-creada)
│   ├── app.log
│   ├── security.log
│   └── errors.log
├── instance/              # ⚠️ LEGACY (migrar BD manualmente)
│   └── consultorio.db
├── docs/
├── tests/
├── run.py
├── version.txt           # ✅ NUEVO
├── LEEME.txt             # ✅ NUEVO
└── Florens.spec          # ✅ NUEVO
```

### En producción (PyInstaller):
```
Florens/
├── Florens.exe
├── _internal/            # Librerías (auto-generado)
├── config/
│   └── settings.ini
├── data/                 # Auto-creada al primer uso
│   ├── consultorio.db
│   └── backups/
├── logs/                 # Auto-creada al primer uso
├── version.txt
└── LEEME.txt
```

---

## 🔄 MIGRACIÓN DE DATOS (MANUAL)

### Opción 1: Mover base de datos existente
```powershell
# Crear carpeta data/ si no existe
mkdir data

# Mover base de datos
Move-Item instance/consultorio.db data/consultorio.db

# Mover backups
Move-Item instance/backups data/backups -Recurse
```

### Opción 2: Dejar que el sistema cree una nueva
- Al iniciar, creará `data/consultorio.db` vacía
- Restaurar desde backup de `instance/backups/` usando panel de Admin

---

## 🧪 PRUEBAS NECESARIAS

### Verificar funcionamiento en desarrollo:
- [ ] Iniciar con `python run.py`
- [ ] Verificar que crea carpetas `data/` y `logs/`
- [ ] Verificar que `config/settings.ini` existe
- [ ] Acceder al sistema y probar funciones básicas:
  - [ ] Login
  - [ ] Crear paciente
  - [ ] Crear turno
  - [ ] Crear prestación
  - [ ] Dashboard financiero
- [ ] Verificar logs en `logs/app.log`
- [ ] Verificar versión en footer de la web
- [ ] Crear backup desde Admin
- [ ] Verificar que backup está en `data/backups/`

### Verificar rutas dinámicas:
```python
from app.config import PathManager

print(f"Base: {PathManager.get_base_dir()}")
print(f"Data: {PathManager.get_data_dir()}")
print(f"Logs: {PathManager.get_logs_dir()}")
print(f"DB: {PathManager.get_db_path()}")
print(f"Frozen: {PathManager.is_frozen()}")
```

---

## 🚀 PRÓXIMOS PASOS (FASE 7)

### 1. Testing completo del sistema reestructurado
- [ ] Ejecutar tests: `pytest tests/`
- [ ] Verificar que no hay errores de rutas
- [ ] Comprobar que backups funcionan

### 2. Primera build con PyInstaller
```powershell
# Instalar PyInstaller
pip install pyinstaller

# Limpiar builds anteriores
Remove-Item -Recurse -Force build, dist

# Generar ejecutable
pyinstaller Florens.spec

# Resultado en:
# dist/Florens/Florens.exe
```

### 3. Post-build manual
```powershell
cd dist/Florens

# Crear carpetas necesarias (NO incluir BD en build)
mkdir data
mkdir logs

# Copiar archivos adicionales
Copy-Item ..\..\LEEME.txt .
Copy-Item ..\..\version.txt .
```

### 4. Testear ejecutable
```powershell
cd dist/Florens
.\Florens.exe
```

Verificar:
- [ ] Inicia sin errores
- [ ] Crea `data/consultorio.db`
- [ ] Crea carpeta `logs/`
- [ ] UI carga correctamente (templates, CSS)
- [ ] Funciones básicas operan
- [ ] Backups se guardan en `data/backups/`

### 5. Empaquetado final
- [ ] Crear archivo .zip con carpeta Florens/
- [ ] Incluir LEEME.txt en raíz
- [ ] Opcional: crear instalador con Inno Setup o NSIS

---

## ⚠️ PROBLEMAS CONOCIDOS Y SOLUCIONES

### PathManager no encuentra archivos
**Síntoma:** Error "No such file or directory"  
**Causa:** `get_base_dir()` calcula mal la ruta en PyInstaller  
**Solución:** Verificar que `sys.frozen` y `sys._MEIPASS` funcionan correctamente

### Configuración no se carga
**Síntoma:** Usa valores por defecto siempre  
**Causa:** `settings.ini` no existe o está en ubicación incorrecta  
**Solución:** `SettingsLoader` crea archivo automáticamente en primera ejecución

### Templates no se encuentran (404)
**Síntoma:** Error al cargar vistas  
**Causa:** Templates no incluidos en .spec o path incorrecto  
**Solución:** Verificar que `datas` en Florens.spec incluye `('app/templates', 'app/templates')`

### SQLite database locked
**Síntoma:** Error al escribir en BD  
**Causa:** Múltiples instancias del ejecutable  
**Solución:** Cerrar todas las instancias antes de ejecutar

---

## 📊 COMPARACIÓN ANTES/DESPUÉS

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Rutas** | Hardcodeadas (`instance/`, `logs/`) | Dinámicas (PathManager) |
| **Configuración** | En código (.env, os.environ) | Externa (settings.ini) |
| **Versioning** | Sin versión visible | v1.0.0 en footer |
| **Empaquetado** | No preparado | Listo para PyInstaller |
| **Backups** | `instance/backups/` | `data/backups/` |
| **Base de datos** | `instance/consultorio.db` | `data/consultorio.db` |
| **Portabilidad** | Requiere Python | Ejecutable standalone |

---

## 🎯 BENEFICIOS DE LA REESTRUCTURACIÓN

1. ✅ **Separación clara**: Código vs Datos vs Configuración
2. ✅ **Portable**: Funciona desde código y ejecutable
3. ✅ **Configurable**: Usuario puede editar settings.ini sin tocar código
4. ✅ **Versionado**: Versión visible para soporte
5. ✅ **Profesional**: Estructura estándar para aplicaciones de escritorio
6. ✅ **Mantenible**: Rutas centralizadas, fácil de actualizar
7. ✅ **Seguro**: SECRET_KEY única por instalación

---

## 📝 NOTAS IMPORTANTES

- ⚠️ **La carpeta `instance/` queda como legacy**: Migrar datos manualmente a `data/`
- ⚠️ **No commitear `data/` ni `config/settings.ini`**: Datos locales y configuración personal
- ⚠️ **Primera ejecución crea estructura**: `data/`, `logs/`, `config/` se auto-crean
- ⚠️ **SECRET_KEY se genera automáticamente**: Cada instalación tiene su propia clave

---

## 🧠 PARA COPILOT

Esta reestructuración prepara el proyecto para:
1. Empaquetado con PyInstaller
2. Distribución como aplicación de escritorio
3. Configuración externa sin modificar código
4. Mejor separación de responsabilidades

Próxima fase: **FASE 7 - Deploy y Packaging** (ver RoadmapFlorens.md)
