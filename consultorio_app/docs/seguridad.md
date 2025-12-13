# 🔐 Seguridad - OdontoApp

**Última actualización:** Diciembre 2025  
**Propósito:** Documentar políticas y medidas de seguridad para datos clínicos sensibles.

---

## ⚠️ ADVERTENCIA CRÍTICA

Este sistema maneja **datos de salud protegidos** (PHI - Protected Health Information).

**Responsabilidades legales:**
- Ley de Protección de Datos Personales (Argentina - Ley 25.326)
- Secreto profesional médico
- Obligación de confidencialidad

**Consecuencias de violación:**
- Responsabilidad civil
- Sanciones administrativas
- Inhabilitación profesional

---

## 🎯 Principios de Seguridad

### 1. Local-First (Datos en Equipo Local)

**Decisión:** Los datos NUNCA salen del equipo local.

**Razones:**
- ✅ Control total del consultorio sobre sus datos
- ✅ Sin riesgo de hackeo a servidores cloud
- ✅ Sin dependencia de proveedores externos
- ✅ Cumplimiento de privacidad por diseño

**Implicaciones:**
- Backup es responsabilidad del consultorio
- Acceso remoto requiere VPN segura (no exponer BD)
- Multi-sucursal requiere replicación manual segura

---

### 2. Least Privilege (Mínimo Privilegio)

**Principio:** Cada usuario ve y hace solo lo estrictamente necesario.

#### Roles Definidos

| Rol | Puede Ver | Puede Hacer | NO Puede |
|-----|-----------|-------------|----------|
| **OWNER** | Todo | Todo | - |
| **ODONTOLOGA** | Pacientes, turnos, operaciones | CRUD completo de datos clínicos | Ver logs técnicos, cambiar roles |
| **TECH_ADMIN** | Logs técnicos, BD stats | Backups, restore, updates | Ver pacientes, DNI, operaciones |

**Implementación:**
```python
@require_role(['OWNER', 'ODONTOLOGA'])
def ver_paciente(id):
    # Solo OWNER y ODONTOLOGA pueden ver pacientes
    pass

@require_role(['OWNER', 'TECH_ADMIN'])
def ver_logs_tecnicos():
    # Solo OWNER y TECH_ADMIN pueden ver logs
    pass
```

---

### 3. Defense in Depth (Defensa en Profundidad)

**Capas de seguridad:**

1. **Autenticación:** Usuario + contraseña
2. **Autorización:** Roles y permisos
3. **Validación:** Input sanitization
4. **Encriptación:** Passwords hasheadas
5. **Auditoría:** Logs de cambios críticos
6. **Backup:** Recuperación ante desastres

---

## 🔑 Autenticación

### Passwords

**Requisitos mínimos:**
- Longitud: 8 caracteres
- Complejidad: 1 mayúscula, 1 número, 1 símbolo
- Almacenamiento: Hash con `bcrypt` (cost factor 12)
- Nunca almacenar en texto plano

**Implementación:**
```python
from bcrypt import hashpw, gensalt, checkpw

# Crear usuario
password_hash = hashpw(password.encode('utf-8'), gensalt(12))

# Verificar login
if checkpw(password.encode('utf-8'), stored_hash):
    # Login exitoso
```

### Sesiones

**Configuración:**
- Timeout: 4 horas de inactividad
- Cookie: HttpOnly, Secure (si HTTPS), SameSite=Lax
- Secreto: `SECRET_KEY` aleatorio de 32 bytes

**Implementación:**
```python
from flask import Flask
from flask_login import LoginManager

app.config['SECRET_KEY'] = os.urandom(32).hex()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)
```

---

## 🛡️ Autorización

### Decorador de Roles

```python
from functools import wraps
from flask import abort
from flask_login import current_user

def require_role(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # No autenticado
            if current_user.role not in roles:
                abort(403)  # No autorizado
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Uso en Rutas

```python
@main_bp.route('/pacientes/<int:id>')
@require_role(['OWNER', 'ODONTOLOGA'])
def ver_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    return render_template('pacientes/detalle.html', paciente=paciente)
```

---

## 🧹 Sanitización de Datos

### Validación de Input

**Reglas:**
- ✅ Validar tipo de dato (int, string, date)
- ✅ Validar formato (DNI, email, teléfono)
- ✅ Validar rango (fecha futura para turnos)
- ✅ Escapar HTML (prevenir XSS)
- ❌ NUNCA confiar en input del usuario

**Implementación:**
```python
from flask_wtf import FlaskForm
from wtforms import StringField, DateField
from wtforms.validators import DataRequired, Length, Regexp

class PacienteForm(FlaskForm):
    dni = StringField('DNI', validators=[
        DataRequired(),
        Length(min=7, max=8),
        Regexp(r'^\d+$', message='Solo números')
    ])
    fecha_nac = DateField('Fecha Nacimiento', validators=[
        DataRequired()
    ])
```

### Prevención XSS

**Jinja2 auto-escapa HTML:**
```html
{{ paciente.nombre }}  <!-- Auto-escaped -->
{{ paciente.nombre | safe }}  <!-- NO usar sin sanitizar antes -->
```

### Prevención SQL Injection

**SQLAlchemy protege automáticamente:**
```python
# ✅ SEGURO (parametrizado)
Paciente.query.filter_by(dni=user_input).first()

# ❌ INSEGURO (nunca hacer)
db.session.execute(f"SELECT * FROM pacientes WHERE dni = '{user_input}'")
```

---

## 📝 Logging Seguro

### Datos Prohibidos en Logs

**NUNCA loguear:**
- ❌ Nombres/apellidos completos
- ❌ DNI completo
- ❌ Números de carnet de obra social
- ❌ Diagnósticos
- ❌ Montos de operaciones
- ❌ Direcciones completas
- ❌ Contraseñas (ni siquiera hasheadas)

**Permitido:**
- ✅ IDs numéricos: `paciente_id=123`
- ✅ Eventos técnicos: `Error al conectar BD`
- ✅ Acciones de usuario: `user_id=5 cambió estado turno_id=45`
- ✅ Métricas agregadas: `Total turnos hoy: 15`

### Ejemplo de Log Seguro

```python
# ❌ MAL
logger.info(f"Usuario creó paciente {paciente.nombre} {paciente.apellido} DNI {paciente.dni}")

# ✅ BIEN
logger.info(f"Usuario {current_user.id} creó paciente_id={paciente.id}")
```

---

## 🔒 Protección de Base de Datos

### Permisos de Archivo

**SQLite file permissions (Linux/Mac):**
```bash
chmod 600 instance/consultorio.db  # Solo owner puede leer/escribir
```

**Windows:**
- Carpeta `instance/` solo accesible por usuario que ejecuta la app

### Backups Seguros

**Encriptación de backups:**
```python
# Futuro: Encriptar backups con contraseña
from cryptography.fernet import Fernet

def backup_encrypted(password):
    # Crear backup normal
    backup_file = backup_database()
    
    # Encriptar con password del usuario
    key = derive_key_from_password(password)
    encrypt_file(backup_file, key)
```

**Almacenamiento:**
- Backups locales: `instance/backups/`
- Backups externos: Pendrive cifrado, nube privada (Google Drive con contraseña)

---

## 🚨 CSRF Protection

### Flask-WTF CSRF Tokens

**Implementación:**
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

**En formularios:**
```html
<form method="POST">
    {{ form.csrf_token }}  <!-- Token automático -->
    <!-- resto del form -->
</form>
```

**Con HTMX:**
```html
<div hx-headers='{"X-CSRFToken": "{{ csrf_token() }}"}'>
    <!-- contenido HTMX -->
</div>
```

---

## 🕵️ Auditoría

### Cambios Críticos a Loguear

**Eventos auditables:**
- ✅ Login/logout
- ✅ Creación de usuario
- ✅ Cambio de rol
- ✅ Cambio de contraseña
- ✅ Eliminación de paciente
- ✅ Cambio de estado de turno
- ✅ Backup/restore de BD

**Implementación:**
```python
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    action = db.Column(db.String(50))  # 'LOGIN', 'DELETE_PATIENT', etc
    entity_type = db.Column(db.String(50))  # 'Paciente', 'Turno', etc
    entity_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    ip_address = db.Column(db.String(50))
```

---

## 🌐 Seguridad de Red (Futuro)

### Si se implementa acceso remoto:

**Requisitos:**
- ✅ HTTPS obligatorio (certificado SSL)
- ✅ VPN o túnel SSH (no exponer app directo)
- ✅ Firewall limitando IPs permitidas
- ✅ Rate limiting (prevenir brute force)
- ❌ NUNCA exponer SQLite a internet

**Alternativa recomendada:**
- VPN (WireGuard, OpenVPN)
- Acceso remoto seguro a equipo local
- No cambiar arquitectura de app

---

## 📋 Checklist de Seguridad

### Antes de Producción

```
[ ] Passwords hasheadas con bcrypt
[ ] SECRET_KEY aleatorio y secreto
[ ] Autenticación implementada (Flask-Login)
[ ] Autorización por roles implementada
[ ] Validación de input en todos los formularios
[ ] CSRF protection habilitado
[ ] Logs sin datos sensibles
[ ] Backups automáticos configurados
[ ] Permisos de archivo correctos (600)
[ ] Tests de seguridad básicos
[ ] Documentación de roles entregada a usuarios
```

---

## 🔮 Seguridad Futura

### Mejoras Planificadas (No Críticas)

1. **Encriptación de BD completa** (SQLCipher)
2. **2FA (Two-Factor Auth)** para rol OWNER
3. **Expiración de contraseñas** (cada 90 días)
4. **Logs de acceso** (quién vio qué paciente)
5. **Firma digital** de backups (verificar integridad)
6. **Audit trail completo** (tabla de cambios históricos)

---

## 📞 Reporte de Vulnerabilidades

**Si detectas una vulnerabilidad de seguridad:**

1. **NO la publiques públicamente**
2. Contactar al desarrollador directamente
3. Incluir:
   - Descripción del problema
   - Pasos para reproducir
   - Impacto potencial
   - Solución propuesta (si tienes)

---

**Última revisión:** Diciembre 2025  
**Responsable:** Equipo de desarrollo OdontoApp
