# 📊 Auditoría de Dependencias: Servicios Viejos vs Nuevos

## Análisis de impacto de eliminar servicios antiguos

### 🔴 Servicios antiguos CRÍTICOS (NO eliminar aún):

#### 1. **paciente_service.py**
**Métodos usados en routes:**
- `listar_pacientes(termino)` → pacientes.py:52 (lista/búsqueda)
- `listar_obras_sociales()` → pacientes.py:117, 353 (carga en formularios)
- `listar_localidades()` → pacientes.py:118, 354 (carga en formularios)
- `crear_paciente(data)` → pacientes.py:128 (crear paciente)
- `obtener_detalle(id)` → pacientes.py:174 (vista detalle completa)
- `actualizar_paciente(paciente, data)` → pacientes.py:333 (editar paciente)
- `obtener_paciente(id)` → pacientes.py:321, turnos.py:31, prestaciones.py:17 (obtener por ID)
- `obtener_o_crear_localidad_por_nombre(nombre)` → pacientes.py:126, 331 (crear localidad)

**REEMPLAZO:**
- `listar_pacientes` → `BuscarPacientesService.buscar(termino)`
- `listar_obras_sociales` → `BuscarObrasSocialesService.listar_todas()`
- `listar_localidades` → `BuscarLocalidadesService.listar_todas()`
- `crear_paciente` → `CrearPacienteService.execute(...)`
- `obtener_detalle` → `BuscarPacientesService.obtener_detalle_completo(id)`
- `actualizar_paciente` → `EditarPacienteService.execute(...)`
- `obtener_paciente` → `BuscarPacientesService.obtener_por_id(id)`
- `obtener_o_crear_localidad_por_nombre` → `CrearLocalidadService.obtener_o_crear(nombre)`

---

#### 2. **turno_service.py**
**Métodos usados en routes:**
- `obtener_semana_agenda(fecha_inicio)` → turnos.py:24 (agenda semanal)
- `listar_turnos_paciente_pagina(id, pagina, por_pagina)` → turnos.py:37 (historial pagina do)
- `crear_turno(data)` → turnos.py:106 (crear turno nuevo)
- `TRANSICIONES_VALIDAS` (constante) → turnos.py:143 (obtener estados permitidos)
- `cambiar_estado(turno_id, estado)` → turnos.py:186 (cambiar estado)
- `eliminar_turno(turno_id)` → turnos.py:216 (eliminar turno)

**REEMPLAZO:**
- `obtener_semana_agenda` → Migrar lógica a servicio específico (no creado aún)
- `listar_turnos_paciente_pagina` → Servicio específico (no creado aún)
- `crear_turno` → `AgendarTurnoService.execute(...)`
- `cambiar_estado` → `CambiarEstadoTurnoService.execute(...)`
- `eliminar_turno` → Servicio específico (no creado aún)
- `TRANSICIONES_VALIDAS` → `CambiarEstadoTurnoService.TRANSICIONES_VALIDAS`

---

#### 3. **odontograma_service.py**
**Métodos usados en routes:**
- `obtener_o_crear_actual(id)` → pacientes.py:184, 226, 252 (obtener actual)
- `obtener_version(paciente_id, odontograma_id)` → pacientes.py:219, 246 (obtener versión)
- `_serializar_odontograma(od)` → pacientes.py:255, 298 (JSON serialization)
- `crear_version_desde(paciente_id, cambios_caras, nota, base_id)` → pacientes.py:282 (crear versión)
- `_ultima_prestacion_timestamp(id)` → pacientes.py:289 (timestamp última prestación)

**REEMPLAZO:**
- `obtener_o_crear_actual` → `ObtenerOdontogramaService.obtener_actual(id)`
- `obtener_version` → `ObtenerOdontogramaService.obtener_version(paciente_id, odontograma_id)`
- `_serializar_odontograma` → Mantener pero mover a helper
- `crear_version_desde` → `CrearVersionOdontogramaService.execute(...)`
- `_ultima_prestacion_timestamp` → Helper interno en servicios

---

#### 4. **prestacion_service.py**
**Métodos usados en routes:**
- `listar_prestaciones()` → prestaciones.py:11 (listar todas)
- `listar_prestaciones_por_paciente_pagina(paciente_id, pagina, por_pagina)` → prestaciones.py:29
- `crear_prestacion(data)` → prestaciones.py:58 (crear prestación)
- `listar_pacientes()` → prestaciones.py:72 (para formulario)
- `listar_practicas_para_paciente(paciente_id)` → prestaciones.py:77 (para formulario)

**REEMPLAZO:**
- `listar_prestaciones_por_paciente_pagina` → `ListarPrestacionesService.listar_por_paciente(id, pagina, por_pagina)`
- `crear_prestacion` → Crear `CrearPrestacionService.execute(...)`
- `listar_pacientes` → `BuscarPacientesService.listar_todos()`
- `listar_practicas_para_paciente` → `ListarPracticasService.listar_todas()`

---

#### 5. **practica_service.py**
**Métodos usados en routes:**
- `listar_por_proveedor(obra_social_id)` → practicas.py:14, 19, 22 (listar prácticas)
- `crear_practica(data)` → practicas.py:39 (crear práctica)
- `obtener_practica(id)` → practicas.py:56 (obtener por ID)
- `actualizar_practica(id, data)` → practicas.py:69 (actualizar)
- `eliminar_practica(id)` → practicas.py:87 (eliminar)

**REEMPLAZO:**
- `listar_por_proveedor` → `ListarPracticasService.listar_todas()` (filtrar en route)
- `crear_practica` → Crear `CrearPracticaService.execute(...)`
- `obtener_practica` → `ListarPracticasService.obtener_por_id(id)`
- `actualizar_practica` → Crear `EditarPracticaService.execute(...)`
- `eliminar_practica` → Crear `EliminarPracticaService.execute(...)`

---

### 🟡 Servicios auxiliares:

#### 6. **turno_utils.py**
- `TurnoValidaciones`
- `FormateoUtils`
- `EstadoTurnoUtils`

**Estado:** Mantener temporalmente (legacy, usar dentro de servicios)

---

#### 7. **busqueda_utils.py**
- `BusquedaUtils.buscar_pacientes_simple(termino)`

**Estado:** Mantener (usada en api.py)

---

### 🟢 Servicios OBSOLETOS (pueden eliminarse):

- `codigo_service.py` - NO se usa en routes
- `estado_service.py` - NO se usa en routes
- `localidad_service.py` - REEMPLAZADO por servicios nuevos

---

## 🎯 Plan de migración segura

### Fase 1: Crear servicios faltantes (ESTA SEMANA)
- `ListarTurnosService.listar_turnos_paciente_pagina()`
- `ObtenerAgendaService.obtener_semana_agenda()`
- `EliminarTurnoService.execute()`
- `CrearPrestacionService.execute()`
- `CrearPracticaService.execute()`
- `EditarPracticaService.execute()`
- `EliminarPracticaService.execute()`

### Fase 2: Refactorizar routes (SIN eliminar servicios viejos)
- Importar servicios NUEVOS en lugar de viejos
- Routes llaman a servicios nuevos
- Servicios viejos quedan sin usar pero presentes

### Fase 3: Validar y eliminar (DESPUÉS de probar)
- Una vez que NO hay imports de servicios viejos en routes
- Eliminar archivos viejos de una vez

---

## 📝 Resumen

**Si eliminamos AHORA los servicios viejos:**
- ❌ Turnos: Se rompe agenda, paginación, creación
- ❌ Pacientes: Se rompe búsqueda, CRUD, detalle
- ❌ Odontogramas: Se rompe cargar/crear versiones
- ❌ Prestaciones: Se rompe listar, crear
- ❌ Prácticas: Se rompe CRUD completo

**Recomendación:**
1. Crear servicios faltantes primero ✅ (en progreso)
2. Refactorizar routes para usar nuevos services
3. Validar que todo funciona
4. ENTONCES sí eliminar viejos en bloque
