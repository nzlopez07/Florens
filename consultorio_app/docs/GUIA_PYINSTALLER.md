# 🚀 GUÍA RÁPIDA - GENERAR EJECUTABLE CON PYINSTALLER

## 📋 Pre-requisitos

✅ Reestructuración completada (PathManager, settings.ini, version.txt)  
✅ Sistema funcionando en desarrollo (`python run.py` sin errores)  
✅ PyInstaller instalado

---

## 🔧 PASO 1: Instalar PyInstaller

```powershell
# Activar entorno virtual
.venv\Scripts\activate

# Instalar PyInstaller
pip install pyinstaller

# Verificar instalación
pyinstaller --version
```

**Versión recomendada:** 6.0+ (compatible con Python 3.9-3.12)

---

## 🏗️ PASO 2: Primera Build

### Limpiar builds anteriores (si existen):
```powershell
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
```

### Generar ejecutable:
```powershell
pyinstaller Florens.spec
```

**Tiempo estimado:** 2-5 minutos (depende del hardware)

### Estructura generada:
```
dist/
└── Florens/
    ├── Florens.exe        # ← Ejecutable principal
    ├── _internal/         # Librerías Python empaquetadas
    │   ├── app/
    │   │   └── templates/ # Templates Jinja2
    │   └── ... (muchos archivos)
    ├── config/
    │   └── settings.ini   # Configuración por defecto
    └── version.txt        # Versión
```

---

## ⚙️ PASO 3: Post-Build Manual

PyInstaller NO crea carpetas vacías, así que hay que crearlas:

```powershell
cd dist\Florens

# Crear carpetas necesarias
New-Item -ItemType Directory -Force -Path data
New-Item -ItemType Directory -Force -Path logs

# Copiar archivos adicionales (si no están en .spec)
Copy-Item ..\..\LEEME.txt . -Force
```

**Estructura final:**
```
dist/Florens/
├── Florens.exe
├── _internal/
├── config/
│   └── settings.ini
├── data/              # ✅ Creada manualmente
├── logs/              # ✅ Creada manualmente
├── version.txt
└── LEEME.txt
```

---

## 🧪 PASO 4: Testear Ejecutable

### Primera ejecución:
```powershell
cd dist\Florens
.\Florens.exe
```

### Qué verificar:

#### 1. Inicio sin errores
- ✅ Ventana de consola se abre (porque `console=True` en .spec)
- ✅ Logs de inicio aparecen:
  ```
  Florens iniciando - LOG_LEVEL=INFO
  Directorio de logs: C:\...\dist\Florens\logs
  Modo: PyInstaller
  ```
- ✅ Mensaje "Servidor iniciado en http://127.0.0.1:5000"

#### 2. Creación automática de archivos
- ✅ Carpeta `data/` contiene `consultorio.db` (creada automáticamente)
- ✅ Carpeta `logs/` contiene archivos .log
- ✅ Si no existía `config/settings.ini`, se crea con valores por defecto

#### 3. Navegador abre automáticamente
- ✅ http://127.0.0.1:5000 carga correctamente
- ✅ Estilos CSS se aplican
- ✅ Footer muestra "Florens v1.0.0"

#### 4. Funcionalidades básicas
- ✅ Login funciona
- ✅ Crear paciente
- ✅ Crear turno
- ✅ Crear prestación
- ✅ Dashboard financiero carga

#### 5. Backups
- ✅ Crear backup desde Admin
- ✅ Archivo se guarda en `data/backups/`
- ✅ Nombre tiene timestamp correcto

---

## ⚠️ TROUBLESHOOTING

### Problema 1: Error "ModuleNotFoundError"
**Síntoma:**
```
ModuleNotFoundError: No module named 'flask_login'
```

**Solución:**
Agregar el módulo faltante a `hiddenimports` en `Florens.spec`:

```python
hidden_imports = [
    'flask_login',  # ← Agregar aquí
    # ... resto
]
```

Luego rebuild:
```powershell
pyinstaller Florens.spec
```

---

### Problema 2: Templates no se encuentran (404)
**Síntoma:**
```
jinja2.exceptions.TemplateNotFound: base.html
```

**Solución:**
Verificar que `datas` en `Florens.spec` incluye templates:

```python
datas = [
    ('app/templates', 'app/templates'),  # ← Verificar esta línea
    # ...
]
```

Si está correcta, verificar que PathManager usa `sys._MEIPASS`:

```python
# En app/config/path_manager.py
if cls.is_frozen():
    return Path(sys._MEIPASS) / 'app'
```

---

### Problema 3: Base de datos no se crea
**Síntoma:**
```
Error: unable to open database file
```

**Solución:**
Verificar permisos de la carpeta `data/`:

```powershell
# Dar permisos de escritura
icacls data /grant Everyone:F
```

O ejecutar como administrador (primera vez).

---

### Problema 4: Ejecutable muy lento al iniciar
**Síntoma:** Tarda 10+ segundos en abrir

**Causa:** PyInstaller descomprime archivos en carpeta temporal

**Soluciones:**
1. **Excluir librerías innecesarias** en `Florens.spec`:
   ```python
   excludes=[
       'numpy',
       'pandas',
       'matplotlib',
       'tkinter',
   ]
   ```

2. **Usar UPX** (ya habilitado en .spec):
   ```python
   upx=True
   ```

3. **Generar ejecutable de un solo archivo** (más lento pero portable):
   ```python
   exe = EXE(
       # ...
       onefile=True,  # ← Un solo .exe
   )
   ```

---

### Problema 5: Logs no se crean
**Síntoma:** Carpeta `logs/` vacía

**Causa:** Permisos o PathManager no detecta correctamente

**Verificar:**
```python
# En consola del ejecutable
from app.config import PathManager
print(PathManager.get_logs_dir())
print(PathManager.is_frozen())  # Debe ser True
```

---

## 🔍 DEBUGGING AVANZADO

### Ver logs de PyInstaller:
```powershell
pyinstaller Florens.spec --log-level DEBUG
```

### Analizar imports faltantes:
```powershell
pyinstaller --debug=imports Florens.spec
```

### Ejecutar con consola visible:
En `Florens.spec`, asegurar:
```python
console=True  # Ver logs en tiempo real
```

Después de debuggear, cambiar a `False` para modo silencioso.

---

## 📦 PASO 5: Empaquetado Final

### Opción 1: ZIP portable
```powershell
# Ir a carpeta dist
cd dist

# Crear archivo ZIP
Compress-Archive -Path Florens -DestinationPath Florens_v1.0.0.zip
```

**Resultado:** `Florens_v1.0.0.zip` (70-150 MB aprox.)

### Opción 2: Instalador con Inno Setup (Avanzado)
1. Descargar Inno Setup: https://jrsoftware.org/isinfo.php
2. Crear script `.iss`:
   ```iss
   [Setup]
   AppName=Florens
   AppVersion=1.0.0
   DefaultDirName={pf}\Florens
   
   [Files]
   Source: "dist\Florens\*"; DestDir: "{app}"; Flags: recursesubdirs
   
   [Icons]
   Name: "{commondesktop}\Florens"; Filename: "{app}\Florens.exe"
   ```
3. Compilar instalador

**Resultado:** `Florens_Setup_v1.0.0.exe` (instalador profesional)

---

## ✅ CHECKLIST DE DISTRIBUCIÓN

Antes de distribuir, verificar:

- [ ] Ejecutable inicia sin errores
- [ ] Todas las funciones principales operan
- [ ] Backups se crean correctamente
- [ ] Versión correcta en footer
- [ ] LEEME.txt incluido
- [ ] Carpetas data/ y logs/ se crean automáticamente
- [ ] settings.ini tiene valores por defecto seguros
- [ ] No hay credenciales hardcodeadas
- [ ] Tamaño del .zip es razonable (< 200 MB)

---

## 📏 OPTIMIZACIÓN DE TAMAÑO

### Tamaño esperado:
- **Carpeta dist/Florens:** 100-200 MB
- **Archivo .zip:** 50-100 MB (comprimido)
- **Instalador .exe:** 60-120 MB

### Para reducir tamaño:
1. **Excluir librerías innecesarias** (numpy, pandas, etc.)
2. **Habilitar UPX** (ya activo en .spec)
3. **Limpiar cache de Python** antes del build:
   ```powershell
   Remove-Item -Recurse -Force __pycache__, .pytest_cache
   ```

---

## 🔄 ACTUALIZAR VERSIÓN

### Antes de generar nueva build:
1. Actualizar `version.txt`:
   ```
   1.0.1
   ```

2. Documentar cambios en `LEEME.txt`

3. Limpiar build anterior:
   ```powershell
   Remove-Item -Recurse -Force build, dist
   ```

4. Rebuild:
   ```powershell
   pyinstaller Florens.spec
   ```

---

## 🎯 RESULTADO FINAL

Después de seguir esta guía, tendrás:

✅ `Florens_v1.0.0.zip` listo para distribuir  
✅ Ejecutable funcionando sin Python instalado  
✅ Configuración externa editable (settings.ini)  
✅ Sistema portable y autónomo  

**Instalación para usuario final:**
1. Descomprimir ZIP
2. Ejecutar Florens.exe
3. ¡Listo! 🎉

---

## 📚 RECURSOS ADICIONALES

- [PyInstaller Official Docs](https://pyinstaller.org/en/stable/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [Florens - REESTRUCTURACION_PYINSTALLER.md](./REESTRUCTURACION_PYINSTALLER.md)
- [Florens - RESUMEN_EJECUTIVO_REESTRUCTURACION.md](./RESUMEN_EJECUTIVO_REESTRUCTURACION.md)

---

**Preparado por:** GitHub Copilot  
**Fecha:** Diciembre 2025  
**Versión:** 1.0.0
