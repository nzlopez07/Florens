# Implementación de Prestaciones IPSS con Autorización y Realización Separadas

**Fecha:** 22/01/2026  
**Contexto:** OdontoApp - Sistema de gestión de consultorio dental  
**Estado:** Análisis y diseño completado. Pendiente: Implementación de modelos y servicios.

---

## 📋 Índice

1. [Problema Inicial](#problema-inicial)
2. [Requerimientos de Negocio](#requerimientos-de-negocio)
3. [Análisis de Excel Actual](#análisis-de-excel-actual)
4. [Brainstorm Inicial](#brainstorm-inicial)
5. [Aclaraciones de Contexto](#aclaraciones-de-contexto)
6. [Estrategia de Integridad de Datos](#estrategia-de-integridad-de-datos)
7. [Baja Lógica de Prácticas](#baja-lógica-de-prácticas)
8. [Diseño de Modelo de Datos](#diseño-de-modelo-de-datos)
9. [Mock Visual Completo](#mock-visual-completo)
10. [Próximos Pasos](#próximos-pasos)

---

## Problema Inicial

La doctora Florencia maneja actualmente un Excel para tracking de pacientes IPSS porque el sistema no permite:

1. Diferenciar **fecha de autorización** vs **fecha de realización** de una prestación
2. Registrar cobros en **múltiples momentos** (consulta inicial + realización posterior)
3. Guardar desglose de pagos: importe afiliado, importe coseguro, importe profesional
4. Calcular sueldo de forma correcta: `honorarios_OS - importe_afiliado + plus_doctora`
5. Validar regla de **12 meses para consulta y limpieza en IPSS**
6. Permitir **edición de prestaciones** (agregar/eliminar/modificar ítems) sin romper auditoría

---

## Requerimientos de Negocio

### Flujo IPSS (2-3 días)

```
DÍA 1 (CONSULTA):
  1. Paciente llega
  2. Doctora hace consulta + identifica tratamientos necesarios
  3. Cobra SOLO plus de consulta
  4. Crea prestación con todos los códigos (consulta, limpieza, prácticas, pluses)
  5. Estado: BORRADOR

DÍA 2 (AUTORIZACIÓN):
  1. OS envía ficha aprobada con:
     - Importe Profesional (honorarios brutos)
     - Importe Afiliado (lo que paga el paciente)
     - Importe Coseguro (si aplica)
  2. Doctora registra fecha de autorización + adjunto (foto ficha)
  3. Estado: AUTORIZADA

DÍA 15 (REALIZACIÓN):
  1. Paciente vuelve para prácticas
  2. Se realiza (consulta ya fue, ahora: extracciones, limpieza, etc.)
  3. Doctora cobra:
     - Plus de prácticas realizadas
     - Plus afiliado (lo que debe el paciente)
  4. Estado: REALIZADA

FIN DE MES (LIQUIDACIÓN):
  Sueldo Doctora = Honorarios OS - Plus Afiliado + Plus Doctora
```

### Ejemplo: Janet Judith Guaimas - IPSS

| Concepto | Monto |
|----------|-------|
| Consulta | $5,000 |
| 2 Extracciones | $30,000 |
| Limpieza | $10,000 |
| **Subtotal actos** | **$45,000** |
| Plus Consulta (Doctora) | $25,000 |
| Plus 2 Extracciones (Doctora) | $40,000 |
| Plus Limpieza (Doctora) | $10,000 |
| **Subtotal Plus Doctora** | **$75,000** |
| Importe Afiliado (paciente) | $13,071 |
| **Total Prestación** | **$133,071** |

**Sueldo Doctora:**
- Honorarios OS autorizados: $40,000
- Menos: Plus Afiliado cobrado: -$13,071
- Más: Plus Doctora cobrados: +$75,000
- **Total a pagar:** $101,928.72

---

## Análisis de Excel Actual

La doctora maneja columnas:
- **Paciente** (nombre)
- **01.03** (consulta - código IPSS)
- **05.02** (limpieza - código IPSS)
- **Códigos extras** (prácticas específicas)
- **Importe Afiliado** (lo que paga el paciente)
- **Plus** (honorarios doctora)
- **Observaciones** (integral = consulta + limpieza, adp = adelanto de pago, etc.)
- **Total Ficha** (suma final)

**Objetivo:** El Excel debe dejar de existir. Toda esta lógica debe estar en Florens.

---

## Brainstorm Inicial

### Ideas para modelar el flujo

1. **Estados de prestación como "puertas"**
   - `borrador`: edición libre
   - `autorizada`: bloquear cambios estructurales (solo anular ítems)
   - `realizada`: solo lectura
   - `liquidada`: cierre de ciclo

2. **Ítems nunca se borran**
   - Marcar como `anulado` (no DELETE)
   - Auditoría completa de cambios
   - Informes pueden filtrar `WHERE estado_item != 'anulado'`

3. **Historial de cobros en tabla separada**
   - `PrestacionCobro`: múltiples registros por tipo (plus_consulta, plus_practica, plus_afiliado)
   - Permite cobros en diferentes días sin modificar cabecera
   - Reportes auditan cobros por período

4. **Auditoría de cambios sensibles**
   - `PrestacionAudit`: registra cambios post-autorización
   - Campo anterior → campo nuevo
   - Razonamiento y usuario que realizó cambio

5. **Validaciones en servicios**
   - EditarPrestacion: chequea estado
   - RegistrarCobro: valida montos
   - CrearPrestacion: valida regla 12 meses IPSS

---

## Aclaraciones de Contexto

### Importante: La autorización NO tiene número

- La OS solo envía una **foto de la misma ficha** que envió la doctora
- Desglose: importe afiliado + importe coseguro + importe profesional
- **NO hay número de autorización** a guardar
- Solo es un checkpoint: llegó o no la ficha aprobada

### La obra social ya está ligada

- Paciente tiene `obra_social_id`
- Prácticas heredan obra social del paciente
- No necesitamos duplicar `obra_social_id` en prestación (solo para referencia rápida)

### Edición de prestaciones

- Permitir en estado `borrador` (sin límites)
- En estado `autorizada`:
  - Bloquear agregar/eliminar ítems de negocio
  - Permitir anular ítems específicos
  - Permitir ajustar importes autorizados (por si OS hace correcciones)
- En estado `realizada`/`liquidada`: solo lectura

---

## Estrategia de Integridad de Datos

### Preservar informes sin romper

**Cambio permitido:** Añadir campos nuevos a tablas existentes  
**Cambio no permitido:** Borrar o renombrar campos existentes

### Tabla `Prestacion` (nuevos campos)

```sql
estado VARCHAR(20) NOT NULL DEFAULT 'borrador'
  -- Enum: borrador | autorizada | realizada | liquidada

fecha_solicitud DATE NOT NULL DEFAULT TODAY
  -- Día que se crea (normalmente = fecha de consulta)

fecha_autorizacion DATE NULL
  -- Cuándo llegó la ficha aprobada

fecha_realizacion DATE NULL
  -- Cuándo se atendió efectivamente

importe_afiliado_autorizado FLOAT NULL
  -- Lo que debe pagar el paciente (según OS)

importe_coseguro_autorizado FLOAT NULL
  -- Coseguro si aplica

importe_profesional_autorizado FLOAT NULL
  -- Honorarios brutos autorizados (sin descontar plus afiliado)

autorizacion_adjunta_path VARCHAR(255) NULL
  -- Ruta a foto/PDF de ficha autorizada

observaciones_autorizacion TEXT NULL
  -- Notas sobre autorización
```

**Constraints:**
- `fecha_realizacion >= fecha_autorizacion` (si ambas existen)
- No permitir estado `realizada` sin `fecha_autorizacion`
- No permitir estado `liquidada` sin `fecha_realizacion`

### Tabla `PrestacionPractica` (nuevos campos)

```sql
tipo_concepto VARCHAR(20) NOT NULL DEFAULT 'acto'
  -- Enum: acto | plus_doctora | plus_afiliado | honorario_os

estado_item VARCHAR(20) NOT NULL DEFAULT 'pendiente'
  -- Enum: pendiente | autorizado | realizado | anulado

monto_autorizado FLOAT NULL
  -- Monto autorizado por OS para este ítem

monto_cobrado FLOAT NULL
  -- [LEGACY] Mantener para compatibilidad; preferir PrestacionCobro

fecha_realizacion_item DATE NULL
  -- Cuándo se realizó este ítem específico

fecha_anulacion DATE NULL
  -- Cuándo se anuló

razon_anulacion VARCHAR(255) NULL
  -- Por qué se anuló
```

**Cambio clave:** `cantidad` Integer permite repetir prácticas (2 extracciones, 3 obturaciones, etc.)

### Nueva tabla `PrestacionCobro`

```sql
CREATE TABLE prestacion_cobro (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  prestacion_id INTEGER NOT NULL FK -> Prestacion,
  fecha_cobro DATE NOT NULL,
  tipo_cobro VARCHAR(30) NOT NULL
    -- Enum: plus_consulta | plus_practica | plus_afiliado | honorario_os | otro,
  monto FLOAT NOT NULL CHECK(monto >= 0),
  razon VARCHAR(255) NULL
    -- "Plus consulta día 1", "Plus 2 extracciones", etc.,
  usuario_id INTEGER NULL FK -> Usuario,
  created_at DATETIME NOT NULL DEFAULT NOW()
)
```

**Queries tipicas:**
```sql
-- Total plus doctora de una prestación
SELECT SUM(monto) FROM prestacion_cobro 
WHERE prestacion_id = X 
  AND tipo_cobro IN ('plus_consulta', 'plus_practica')

-- Total plus afiliado cobrado en período
SELECT SUM(monto) FROM prestacion_cobro 
WHERE tipo_cobro = 'plus_afiliado' 
  AND fecha_cobro BETWEEN fecha1 AND fecha2
```

### Nueva tabla `PrestacionAudit` (opcional)

```sql
CREATE TABLE prestacion_audit (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  prestacion_id INTEGER NOT NULL FK -> Prestacion,
  campo VARCHAR(50) NOT NULL,
  valor_anterior TEXT NULL,
  valor_nuevo TEXT NULL,
  fecha_cambio DATETIME NOT NULL DEFAULT NOW(),
  razon VARCHAR(255) NULL,
  usuario_id INTEGER NULL FK -> Usuario
)
```

**Uso:**
- Registrar cambios de importes autorizados post-autorización
- Tracking de anulaciones de ítems
- Auditoría completa para compliance

---

## Baja Lógica de Prácticas

### Problema

Si la doctora da de baja una práctica (porque no la realiza más), y esa práctica ya está en prestaciones antiguas:
- **Borrar físicamente**: rompe prestaciones históricas
- **Ignorar**: sigue apareciendo en búsquedas y menús

### Solución: Baja Lógica

**Nuevos campos en tabla `Practica`:**

```sql
activa BOOLEAN NOT NULL DEFAULT TRUE
  -- FALSE = práctica dada de baja (no se puede usar en nuevas prestaciones)

fecha_baja DATE NULL
  -- Cuándo se dio de baja

razon_baja VARCHAR(255) NULL
  -- Por qué se dio de baja
```

**Reglas:**
- Listar prácticas disponibles: `WHERE activa = TRUE`
- Mostrar todas (para auditoría): incluir `activa = FALSE`
- FK a prestación antigua sigue siendo válida (integridad referencial)

**Servicios afectados:**

1. `DarBajaPracticaService` (renombrar `EliminarPracticaService`)
   - Set `activa = FALSE`, `fecha_baja = TODAY`, `razon_baja = X`
   - No borrar; permitir aunque tenga prestaciones asociadas

2. `ListarPracticasService`
   - Parámetro `incluir_inactivas=False` (default)
   - Query: `WHERE activa = TRUE`

3. `CrearPracticaService`
   - Default `activa = TRUE`

---

## Diseño de Modelo de Datos

### Cambios en `app/models/prestacion.py`

```python
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from app.database import db
from enum import Enum as PyEnum

class EstadoPrestacion(PyEnum):
    BORRADOR = 'borrador'
    AUTORIZADA = 'autorizada'
    REALIZADA = 'realizada'
    LIQUIDADA = 'liquidada'

class Prestacion(db.Model):
    __tablename__ = "prestaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    paciente = relationship("Paciente", back_populates="prestaciones")
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, nullable=False)
    observaciones = Column(String, nullable=True)
    
    # NUEVOS CAMPOS IPSS
    estado = Column(String(20), nullable=False, default='borrador')
    fecha_solicitud = Column(Date, nullable=False)  # Día de creación
    fecha_autorizacion = Column(Date, nullable=True)  # Llegó ficha aprobada
    fecha_realizacion = Column(Date, nullable=True)  # Se atendió
    importe_afiliado_autorizado = Column(Float, nullable=True)
    importe_coseguro_autorizado = Column(Float, nullable=True)
    importe_profesional_autorizado = Column(Float, nullable=True)
    autorizacion_adjunta_path = Column(String(255), nullable=True)
    observaciones_autorizacion = Column(String, nullable=True)
    
    # Relaciones
    turnos = relationship("Turno", back_populates="prestacion")
    practicas_assoc = relationship("PrestacionPractica", back_populates="prestacion", cascade="all, delete-orphan")
    cobros = relationship("PrestacionCobro", back_populates="prestacion", cascade="all, delete-orphan")
    audits = relationship("PrestacionAudit", back_populates="prestacion", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("fecha_realizacion IS NULL OR fecha_autorizacion IS NULL OR fecha_realizacion >= fecha_autorizacion"),
    )
```

### Cambios en `app/models/prestacion_practica.py`

```python
from sqlalchemy import Column, Integer, Float, ForeignKey, String, Date, Enum
from sqlalchemy.orm import relationship
from app.database import db
from enum import Enum as PyEnum

class TipoConcepto(PyEnum):
    ACTO = 'acto'
    PLUS_DOCTORA = 'plus_doctora'
    PLUS_AFILIADO = 'plus_afiliado'
    HONORARIO_OS = 'honorario_os'

class EstadoItem(PyEnum):
    PENDIENTE = 'pendiente'
    AUTORIZADO = 'autorizado'
    REALIZADO = 'realizado'
    ANULADO = 'anulado'

class PrestacionPractica(db.Model):
    __tablename__ = "prestacion_practica"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prestacion_id = Column(Integer, ForeignKey("prestaciones.id"), nullable=False)
    practica_id = Column(Integer, ForeignKey("practicas.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)  # PERMITE MÚLTIPLES
    monto_unitario = Column(Float, nullable=True)
    observaciones = Column(String, nullable=True)
    
    # NUEVOS CAMPOS IPSS
    tipo_concepto = Column(String(20), nullable=False, default='acto')
    estado_item = Column(String(20), nullable=False, default='pendiente')
    monto_autorizado = Column(Float, nullable=True)
    monto_cobrado = Column(Float, nullable=True)  # LEGACY
    fecha_realizacion_item = Column(Date, nullable=True)
    fecha_anulacion = Column(Date, nullable=True)
    razon_anulacion = Column(String, nullable=True)

    prestacion = relationship("Prestacion", back_populates="practicas_assoc")
    practica = relationship("Practica", back_populates="prestaciones_assoc")
```

### Nueva tabla `PrestacionCobro`

```python
# app/models/prestacion_cobro.py
from sqlalchemy import Column, Integer, Float, ForeignKey, String, Date, DateTime
from sqlalchemy.orm import relationship
from app.database import db
from datetime import datetime

class PrestacionCobro(db.Model):
    __tablename__ = "prestacion_cobro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prestacion_id = Column(Integer, ForeignKey("prestaciones.id"), nullable=False)
    fecha_cobro = Column(Date, nullable=False)
    tipo_cobro = Column(String(30), nullable=False)  # plus_consulta, plus_practica, plus_afiliado, honorario_os, otro
    monto = Column(Float, nullable=False, default=0.0)
    razon = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    prestacion = relationship("Prestacion", back_populates="cobros")
```

### Nueva tabla `PrestacionAudit` (opcional)

```python
# app/models/prestacion_audit.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import db
from datetime import datetime

class PrestacionAudit(db.Model):
    __tablename__ = "prestacion_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prestacion_id = Column(Integer, ForeignKey("prestaciones.id"), nullable=False)
    campo = Column(String(50), nullable=False)
    valor_anterior = Column(Text, nullable=True)
    valor_nuevo = Column(Text, nullable=True)
    fecha_cambio = Column(DateTime, nullable=False, default=datetime.utcnow)
    razon = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    prestacion = relationship("Prestacion", back_populates="audits")
```

### Cambios en `app/models/practica.py`

```python
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint, Boolean, Date
from sqlalchemy.orm import relationship
from app.database import db

class Practica(db.Model):
    __tablename__ = "practicas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(30), nullable=False)
    descripcion = Column(String(200), nullable=False)
    proveedor_tipo = Column(String(20), nullable=False)
    obra_social_id = Column(Integer, ForeignKey("obras_sociales.id"), nullable=True)
    monto_unitario = Column(Float, nullable=False, default=0.0)
    
    # NUEVOS CAMPOS BAJA LÓGICA
    activa = Column(Boolean, nullable=False, default=True)
    fecha_baja = Column(Date, nullable=True)
    razon_baja = Column(String(255), nullable=True)

    obra_social = relationship("ObraSocial", back_populates="practicas", foreign_keys=[obra_social_id])
    prestaciones_assoc = relationship("PrestacionPractica", back_populates="practica")

    __table_args__ = (
        UniqueConstraint('proveedor_tipo', 'obra_social_id', 'codigo', name='uq_practica_codigo_por_proveedor'),
    )
```

---

## Mock Visual Completo

Ver archivo: [docs/mock_prestaciones_ipss.txt](../docs/mock_prestaciones_ipss.txt)

Incluye:
- Definición detallada de todas las tablas
- Ejemplo real (Janet Judith Guaimas) con 2 extracciones
- Timeline completo (solicitud → autorización → realización → liquidación)
- Caso de anulación de ítem
- Query de validación de 12 meses IPSS
- Resumen de ventajas del diseño

---

## Próximos Pasos

### Fase 1: Implementación de Modelos ✅ (Este documento)

- [ ] Crear migration o actualizar modelos (agregar campos)
- [ ] Crear nuevas tablas (`PrestacionCobro`, `PrestacionAudit`)
- [ ] Actualizar `__init__.py` en models para exportar nuevas clases

### Fase 2: Servicios Nuevos/Modificados

**Prácticas:**
- [ ] Crear `DarBajaPracticaService` (reemplaza `EliminarPracticaService`)
- [ ] Modificar `ListarPracticasService` (agregar parámetro `incluir_inactivas`)

**Prestaciones:**
- [ ] Extender `CrearPrestacionService` (estado inicial, validar 12 meses IPSS)
- [ ] Crear `EditarPrestacionService` (bloqueos por estado)
- [ ] Crear `AnularItemPrestacionService` (marcar ítem como anulado)
- [ ] Crear `RegistrarAutorizacionPrestacionService` (fecha + importes + adjunto)
- [ ] Crear `RegistrarCobroPrestacionService` (agregar row a `PrestacionCobro`)
- [ ] Crear `RegistrarRealizacionPrestacionService` (marcar realizada)
- [ ] Crear `LiquidarDoctoraService` (calcular sueldo)

**Validaciones:**
- [ ] Crear `ValidarRegla12MesesIPSSService` (consulta, limpieza)
- [ ] Crear `ValidarEstadoPrestacionService` (transiciones permitidas)

### Fase 3: Rutas y UI

- [ ] Agregar ruta POST `/api/prestaciones/<id>/autorizar` (registrar autorización)
- [ ] Agregar ruta POST `/api/prestaciones/<id>/cobro` (registrar cobro)
- [ ] Agregar ruta POST `/api/prestaciones/<id>/realizar` (marcar realizada)
- [ ] Extender template de prestación (timeline, adjuntos, tabla de cobros)
- [ ] Agregar modal de "Registrar autorización" (fecha + importes + adjunto)

### Fase 4: Reportes y Auditoría

- [ ] Query de liquidación doctora (período)
- [ ] Reporte de prestaciones por estado
- [ ] Reporte de cobros por tipo
- [ ] Tracking de cambios (`PrestacionAudit`)

---

## Excepciones a Actualizar

En `app/services/common/exceptions.py`:

- `EstadoPrestacionInvalidoError`: transición de estado no permitida
- `PrestacionNoAutorizadaError`: intento de realizar sin autorización
- `FechasRealizacionInvalidasError`: `fecha_realizacion < fecha_autorizacion`
- `ReglaIPSSViolada`: consulta/limpieza dentro de 12 meses
- `PracticsaDadaDeBajaError`: intento de usar práctica inactiva en nueva prestación

---

## Integridad y Compatibilidad

✅ **Campos existentes se mantienen:** `monto`, `fecha`, `descripcion`, `observaciones`  
✅ **Nuevos campos son nullable:** migración suave  
✅ **Informes existentes funcionan:** filtros que ignoren nuevos campos siguen válidos  
✅ **Baja lógica de prácticas:** FK a antiguas prestaciones se mantiene válida  
✅ **Ítems nunca se borran:** auditoría y compliance garantizados  

---

## Notas para el Agente Implementador

1. **Orden de implementación:**
   - Primero: Actualizar modelos existentes
   - Segundo: Crear nuevas tablas
   - Tercero: Servicios (en orden de dependencia)
   - Cuarto: Rutas y UI

2. **Testing:**
   - Crear tests para validación de 12 meses IPSS
   - Tests de transiciones de estado
   - Tests de integridad (fecha_realizacion >= fecha_autorizacion)

3. **Migración de datos:**
   - Prestaciones existentes → estado `realizada` (con `fecha_realizacion = fecha`)
   - Prácticas existentes → `activa = TRUE` (por defecto)

4. **Seguridad:**
   - No loguear datos clínicos (solo IDs numéricos)
   - Auditoría de cambios post-autorización para compliance RGPD

---

**Documento versión 1.0**  
Generado: 22/01/2026
