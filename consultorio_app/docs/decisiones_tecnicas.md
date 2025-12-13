# 📐 Decisiones Técnicas - OdontoApp

**Última actualización:** Diciembre 2025  
**Propósito:** Documentar decisiones arquitectónicas clave para mantener consistencia técnica.

---

## 🏗️ Arquitectura General

### Patrón MVC con Separación de Responsabilidades

```
Cliente (Browser)
    ↓
Routes (Controladores)
    ↓
Services (Lógica de negocio)
    ↓
Models (ORM - SQLAlchemy)
    ↓
Database (SQLite)
```

**Reglas:**
- ✅ Routes solo manejan HTTP (request/response)
- ✅ Services contienen toda la lógica de negocio
- ✅ Models solo definen estructura de datos
- ❌ NUNCA lógica de negocio en routes
- ❌ NUNCA queries directas desde routes

---

## 💾 Base de Datos

### SQLite Local-First

**Decisión:** SQLite como base de datos principal.

**Razones:**
1. **Propiedad de datos:** El consultorio mantiene control total de sus datos
2. **Privacidad:** Datos clínicos sensibles nunca salen del equipo local
3. **Simplicidad:** Cero configuración, cero dependencias externas
4. **Portabilidad:** Un archivo `.db` contiene toda la información
5. **Respaldos:** Copiar archivo = backup completo
6. **Sin costos:** No requiere servidor ni suscripciones

**Limitaciones conocidas:**
- ❌ No apto para múltiples usuarios simultáneos (>5)
- ❌ No apto para acceso remoto directo
- ✅ Perfecto para consultorio con 1-3 usuarios locales

**Migración futura (si crece):**
- PostgreSQL para multi-usuario
- Mantener SQLite para versión portable

---

## 🔐 Seguridad y Privacidad

### Principio de Mínimo Privilegio

**Implementación:**
- Roles: `OWNER`, `ODONTOLOGA`, `TECH_ADMIN`
- Cada rol ve solo lo necesario
- `TECH_ADMIN` NO puede ver datos clínicos

### Datos Sensibles en Logs

**Regla de oro:** ❗ NUNCA loguear datos clínicos

**Prohibido en logs:**
- Nombres/apellidos de pacientes
- DNI
- Diagnósticos
- Montos de operaciones
- Direcciones completas

**Permitido:**
- IDs numéricos (paciente_id=123)
- Eventos técnicos (error de BD, fallo de validación)
- Métricas agregadas (total de turnos)

---

## 🗂️ ORM: SQLAlchemy

**Decisión:** SQLAlchemy como ORM único.

**Razones:**
1. Estándar de la industria en Python
2. Type safety con modern Python
3. Migrations con Alembic (futuro)
4. Relaciones explícitas y claras
5. Compatible con múltiples BD

**Reglas de uso:**
- Usar `db.session` para transacciones
- Usar `relationship()` para FK
- Usar `cascade="all, delete"` donde corresponda
- Usar `back_populates` para relaciones bidireccionales

---

## 📦 Backups

### Estrategia de Respaldo

**Regla:** Ningún update sin backup previo.

**Implementación:**
```python
# Antes de cualquier operación destructiva:
backup_database()  # Crea consultorio_backup_TIMESTAMP.db
```

**Frecuencia:**
- **Manual:** Antes de cada update de sistema
- **Automático:** Diario (scheduler)
- **Retención:** Últimos 30 días

**Ubicación:** `instance/backups/`

---

## 🎨 Frontend

### Server-Side Rendering con HTMX

**Decisión:** Jinja2 + Bootstrap + HTMX (no React/Vue)

**Razones:**
1. **Simplicidad:** Equipo Python, no especialistas frontend
2. **Mantenibilidad:** Menos dependencias, menos complejidad
3. **Performance:** SSR es más rápido para CRUD
4. **SEO-friendly:** Contenido renderizado en servidor
5. **HTMX:** Interactividad moderna sin JavaScript complejo

**No usar:**
- ❌ React/Vue/Angular (overkill para CRUD)
- ❌ SPA (no necesario)
- ❌ Build tools complejos (Webpack, etc)

**Cuándo reconsiderar:**
- Si crece a >100 usuarios concurrentes
- Si requiere mobile app nativa
- Si equipo crece con frontend specialist

---

## 🧪 Testing

### Estrategia de Tests

**Prioridad:** Tests de regresión para funcionalidad crítica.

**Mínimos requeridos:**
1. Crear paciente
2. Crear turno
3. Cambio automático de estado a NoAtendido
4. Cambio manual de estado
5. Backup y restore
6. Login/logout (cuando se implemente)

**Herramienta:** `pytest`

**No hacer:**
- ❌ Tests de cobertura 100% (no es eficiente)
- ❌ Tests de UI (frágiles)
- ✅ Tests de lógica de negocio crítica

---

## 📁 Estructura de Carpetas

```
consultorio_app/
├── app/
│   ├── __init__.py          # Factory de Flask
│   ├── database/            # Configuración de BD
│   ├── models/              # Modelos SQLAlchemy
│   ├── routes/              # Controladores (solo HTTP)
│   ├── services/            # Lógica de negocio
│   └── templates/           # Jinja2 templates
├── instance/                # Datos locales (BD, backups)
├── docs/                    # Documentación técnica
├── tests/                   # Tests (futuro)
└── run.py                   # Punto de entrada
```

---

## 🔄 Versionado

### Semantic Versioning (SemVer)

**Formato:** `vX.Y.Z`

- `X` (Major): Cambios incompatibles (ej: cambio de esquema BD)
- `Y` (Minor): Nueva funcionalidad compatible
- `Z` (Patch): Correcciones de bugs

**Ejemplos:**
- `v1.0.0` → Primera versión estable
- `v1.1.0` → Agregar autenticación
- `v1.1.1` → Corregir bug en turnos

---

## 🚫 Anti-Patrones a Evitar

1. **Lógica en templates:** Jinja2 solo para presentación
2. **Queries en routes:** Usar services
3. **Datos hardcodeados:** Usar configuración
4. **Passwords en texto plano:** Siempre hash (bcrypt)
5. **SQL manual:** Usar ORM
6. **Logs verbosos en producción:** Solo ERROR/WARNING

---

## 🎯 Principios de Diseño

### Local-First

Datos viven en el equipo local, no en la nube.

### Least Privilege

Usuario ve solo lo que necesita para su rol.

### Fail-Safe

Error debe ser evidente pero no romper el sistema.

### Backward Compatibility

Updates nunca deben romper datos existentes.

---

## 📝 Convenciones de Código

### Python
- PEP 8 (formateo automático con Black)
- Type hints donde sea útil
- Docstrings para funciones públicas

### SQL/Models
- Nombres en inglés (tabla `patients`, no `pacientes`)
- Snake_case para columnas (`fecha_nac`)
- PascalCase para clases (`Paciente`)

### Templates
- Nombres descriptivos (`pacientes/lista.html`)
- Parciales con prefijo `_` (`_tabla.html`)
- Bootstrap 5.3 para estilos

---

## 🔮 Futuras Decisiones Pendientes

1. **Migraciones:** Alembic vs script manual
2. **Packaging:** PyInstaller vs Electron
3. **Notificaciones:** Email vs SMS vs ninguna
4. **Reportes:** PDF vs Excel vs ambos
5. **Multi-sucursal:** Replicación vs BD centralizada

---

**Última revisión:** Diciembre 2025
