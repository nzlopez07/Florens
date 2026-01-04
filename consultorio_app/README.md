# Florens - Sistema de Gestión Odontológica

**Aplicación desktop local-first para consultorio dental**

**Versión actual:** 1.0.0  
**Última actualización:** Enero 2026

---

## 🚀 Inicio Rápido

### Opción 1: Ejecutable (Recomendado - Sin Python)
```
1. Descargar Florens_v1.0.0.zip
2. Descomprimir carpeta
3. Ejecutar Florens.exe
4. ¡Listo! El navegador se abre automáticamente
```

**Credenciales iniciales:**
- Usuario: `admin` / Contraseña: `admin123` (rol ADMIN)
- Usuario: `florencia` / Contraseña: `emma123` (rol DUEÑA)

### Opción 2: Desde código fuente (Para desarrollo)
```bash
# 1. Activar entorno virtual
.venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar servidor
python run.py

# 4. Acceder a
# - Web: http://127.0.0.1:5000
# - API Docs: http://127.0.0.1:5000/api/docs
```

---

## 📋 Características

✅ Gestión completa de pacientes (CRUD + búsqueda)  
✅ Agenda de turnos con confirmación por WhatsApp  
✅ Odontograma digital interactivo  
✅ Prestaciones y prácticas realizadas  
✅ Dashboard financiero (ingresos/gastos)  
✅ Sistema de backups automáticos  
✅ Logs técnicos para auditoría  
✅ Respeta privacidad: datos 100% locales  
✅ Cierre automático al cerrar última pestaña  

---

## 📁 Estructura de carpetas (EXE)

```
Florens/
├── Florens.exe          ← Ejecutable principal
├── version.txt          ← Versión instalada
├── LEEME.txt            ← Manual de usuario
├── config/
│   └── settings.ini     ← Configuración (logs, WhatsApp, etc.)
├── data/                ← Base de datos (se crea automáticamente)
│   ├── consultorio.db   ← Datos principales
│   └── backups/         ← Copias de seguridad automáticas
└── logs/                ← Registros técnicos (se crean automáticamente)
    ├── app.log
    ├── security.log
    ├── errors.log
    └── whatsapp.log
```

**Estructura de carpetas (Desarrollo):**

```
consultorio_app/
├── app/                    # Código fuente
│   ├── __init__.py        # Configuración Flask
│   ├── models/            # Modelos de BD (Paciente, Turno, etc.)
│   ├── routes/            # Rutas HTTP (index, pacientes, turnos, etc.)
│   ├── services/          # Lógica de negocio
│   ├── database/          # Config BD y utilidades
│   ├── config/            # PathManager, SettingsLoader
│   ├── utils/             # Helpers y utilidades generales
│   └── media/             # Archivos estáticos (íconos, odontograma)
├── config/                # settings.ini (configuración)
├── data/                  # BD y backups (gitignored)
├── logs/                  # Registros técnicos (gitignored)
├── docs/                  # Documentación técnica
├── run.py                 # Punto de entrada
├── version.txt            # Versión
└── Florens.spec          # Configuración PyInstaller
```

---

## 🔐 Seguridad y Privacidad

- ✅ **Todos los datos son locales:** No se envía información a servidores externos
- ✅ **Sin cloud:** Base de datos SQLite en tu carpeta `data/`
- ✅ **Contraseñas hasheadas:** Usando werkzeug.security
- ✅ **Logs sanitizados:** No registra datos clínicos, solo eventos técnicos
- ⚠️ **Respaldos recomendados:** Copia la carpeta `data/` regularmente a un USB o Google Drive

---

## 🔄 Actualización del Sistema

**Antes de actualizar: Hacer backup (icono ⚙️ → Crear respaldo)**

1. Descargar nueva versión ZIP
2. Descomprimir en carpeta aparte (ej. `Florens_v1.1.0/`)
3. Copiar `data/` de versión anterior a la nueva
4. Copiar `config/settings.ini` (conserva tu configuración)
5. Ejecutar nuevo `Florens.exe`
6. El sistema aplicará migraciones automáticamente

**Rollback:** Si algo falla, ejecutar la versión anterior.

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [LEEME.txt](LEEME.txt) | Manual de usuario (español) |
| [docs/decisiones_tecnicas.md](docs/decisiones_tecnicas.md) | Arquitectura del sistema |
| [docs/seguridad.md](docs/seguridad.md) | Políticas de seguridad |
| [docs/roadmap.md](docs/roadmap.md) | Plan de desarrollo futuro |
| [docs/WHATSAPP_SETUP.md](docs/WHATSAPP_SETUP.md) | Integración WhatsApp |

---

## 🛠 Desarrollo

### Instalar en entorno de desarrollo
```bash
pip install -r requirements.txt
```

### Empaquetar como EXE (PyInstaller)
```bash
pyinstaller --clean Florens.spec
```

El resultado estará en `dist/Florens/`

### Ejecutar tests
```bash
pytest tests/
```

---

## 📦 Distribución

**Entrega de una nueva versión:**

1. Incrementar `version.txt`
2. Build limpio: `pyinstaller --clean Florens.spec`
3. Empaquetar: comprimir `dist/Florens/` como `Florens_vX.Y.Z.zip`
4. Publicar: incluir `LEEME.txt`, checksum SHA256, e instrucciones de actualización

---

## 🤝 Contribuciones

Desarrollado para **Dra. Florencia López** - Odontología General.  
Equipo: Nicolás López (desarrollo)

---

## 📝 Licencia

Privado. Uso exclusivo para consultorio dental.

---

## 🆘 Soporte

Para problemas técnicos:
- Revisar `logs/errors.log` en carpeta Florens
- Hacer backup y restaurar desde punto anterior si es necesario
- Contactar con soporte técnico
