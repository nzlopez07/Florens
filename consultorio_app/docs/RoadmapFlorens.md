# 🗺️ Roadmap de Calidad — Florens
## Sistema de Gestión Dental (Local-First)

**Proyecto:** Florens – Sistema de Gestión Dental  
**Autor:** Nicolás López  
**Contexto:** Software clínico real para un consultorio odontológico  
**Estado actual:** Funcionalmente maduro, entrando en etapa de **deploy y operación**  
**Objetivo:** entregar un sistema **estable, seguro, mantenible y desplegable**, apto para uso real con datos clínicos sensibles.

---

## 🎯 Principios rectores (NO negociables)

Estos principios gobiernan todas las decisiones técnicas del proyecto:

- Arquitectura en capas: **Routes → Services → Models**
- Services desacoplados del framework (Flask es solo infraestructura)
- Datos clínicos **local-first** (la información pertenece al consultorio)
- Seguridad por diseño (autenticación, roles, mínimo privilegio)
- **Ninguna actualización sin backup previo**
- Logs técnicos **sin datos sensibles**
- Evolución controlada sin romper datos (*Backward Compatibility*)
- Deploy como **aplicación de escritorio**, no SaaS ni cloud

> 📌 Florens **no compite en el mercado de software odontológico**.  
> Es una solución **hecha a medida**, con estándares profesionales.

---

## 🧱 FASE 0 — Preparación del proyecto (contexto para Copilot) ✅

**Objetivo:** que cualquier desarrollador (y Copilot) entienda claramente  
la arquitectura, las decisiones tomadas y los límites del sistema.

- [x] Carpeta `/docs`
- [x] Documentación técnica y funcional
- [x] Decisiones explícitas documentadas:
  - Base de datos local (SQLite)
  - Arquitectura MVC + Services
  - Frontend server-side (Jinja / HTMX)
  - No deploy web público
- [x] Naming definitivo del sistema: **Florens**

**Estado:** ✅ COMPLETADA

---

## 🔐 FASE 1 — Autenticación ✅

**Objetivo:** impedir acceso no autorizado al sistema.

- [x] Modelo `Usuario`
- [x] Hash seguro de contraseñas
- [x] Login / Logout
- [x] Manejo de sesión
- [x] Protección de rutas

**Estado:** ✅ COMPLETADA

---

## 🧑‍⚕️ FASE 2 — Autorización por roles ✅

**Roles definidos:**

- `DUEÑA` → acceso clínico + financiero  
- `ODONTOLOGA` → acceso clínico  
- `ADMIN` → soporte técnico (sin acceso a datos clínicos)

- [x] Control de acceso centralizado
- [x] Restricción de finanzas solo para `DUEÑA`
- [x] Separación clara entre dominio clínico y técnico

**Estado:** ✅ COMPLETADA

---

## 🧪 FASE 3 — Validaciones y reglas de negocio ✅

**Objetivo:** garantizar consistencia y calidad de los datos.

- [x] Validaciones con Flask-WTF
- [x] Reglas de negocio centralizadas en Services
- [x] Prevención de turnos inválidos o solapados
- [x] UX robusta (mensajes claros, preservación de datos)

**Estado:** ✅ COMPLETADA

---

## 💰 FASE 3.5 — Gestión financiera avanzada ✅

**Objetivo:** control real del flujo económico del consultorio.

- [x] Dashboard financiero
- [x] Separación Particular / Obras Sociales
- [x] Análisis por período y práctica
- [x] Acceso restringido por rol

**Estado:** ✅ COMPLETADA

---

## 🔄 FASE 3.7 — Estados de Turno normalizados ✅

**Objetivo:** consistencia del dominio y de las transiciones de estado.

- [x] Estados modelados como FK (`estado_id`)
- [x] Lógica de cambio de estado centralizada en Services
- [x] Scheduler adaptado al nuevo modelo
- [x] Compatibilidad temporal con columna legacy

**Estado:** ✅ COMPLETADA  
⚠️ Pendiente futuro: limpieza definitiva de columna legacy en producción

---

## 🧾 FASE 4 — Logging técnico seguro ✅

**Objetivo:** permitir soporte remoto sin comprometer datos clínicos.

- [x] Logs separados por tipo (app, security, errors)
- [x] Sanitización de datos sensibles
- [x] Acceso a logs restringido (Admin / Dueña)
- [x] Helpers de logging reutilizables

**Estado:** ✅ COMPLETADA

---

## ⏱️ FASE 5 — Scheduler (tareas automáticas) ✅

**Objetivo:** mantener consistencia temporal sin intervención manual.

- [x] APScheduler
- [x] Actualización automática de turnos vencidos
- [x] Limpieza de estados temporales
- [x] Frecuencia segura (ej. cada 5 minutos)

**Estado:** ✅ COMPLETADA

---

## 🧪 FASE 6 — Testing estratégico 🟡

**Objetivo:** permitir evolución sin romper el sistema.

- [x] Tests de services críticos
- [x] Tests de rutas principales
- [x] Tests de finanzas
- [ ] Pendiente:
  - edición / eliminación compleja
  - odontograma
  - backup + restore end-to-end
  - reducción de warnings ORM

**Estado:** 🟡 EN PROGRESO  
(No bloquea el deploy inicial)

---

## 📦 FASE 7 — Deploy y Packaging 🔴 (PRIORIDAD ACTUAL)

**Objetivo:** entregar Florens como aplicación de escritorio local.

### Alcance explícito

- ❌ No SaaS
- ❌ No servidor remoto
- ❌ No Docker para cliente
- ✅ Aplicación local ejecutable
- ✅ Base de datos local
- ✅ Soporte remoto eventual

### Tareas

- [ ] Definir estructura final de carpetas:
  ```
  /app      → código
  /data     → base de datos y backups
  /logs     → logs
  /config   → configuración externa
  ```
- [ ] Externalizar configuración (paths, flags)
- [ ] Crear carpetas automáticamente si no existen
- [ ] Empaquetar con **PyInstaller**
- [ ] Verificar ejecución sin Python instalado
- [ ] Mostrar versión visible en la UI

**Estado:** ⏳ LISTO PARA INICIAR

---

## 💾 FASE 7.5 — Sistema de Backups (CRÍTICO)

**Objetivo:** proteger datos clínicos ante fallos o errores humanos.

- [ ] Backup automático de la base de datos
- [ ] Timestamp en nombre de archivo
- [ ] Retención limitada (últimos N backups)
- [ ] Restore manual (solo rol `DUEÑA`)
- [ ] Backup obligatorio previo a cualquier update

> ❗ Regla absoluta: **nunca ejecutar una nueva versión sin backup previo**

---

## 🔄 FASE 8 — Sistema de actualizaciones seguras

**Objetivo:** mantener el sistema sin riesgo de pérdida de datos.

- [ ] Versionado semántico visible (`vX.Y.Z`)
- [ ] Actualización asistida (manual)
- [ ] Migraciones controladas si fueran necesarias
- [ ] Compatibilidad hacia atrás

⚠️ No auto-update silencioso  
⚠️ No pérdida de control  
⚠️ No sincronización forzada a la nube

---

## 📋 Estado general del proyecto

```
[x] Arquitectura madura
[x] Seguridad y roles
[x] Dominio clínico sólido
[x] Finanzas reales
[x] Logging y soporte
[x] Scheduler
[~] Testing
[ ] Deploy
[ ] Backups
[ ] Updates
```

---

## 🧠 Nota importante para Copilot

Este proyecto:

- es **local-first**
- es **para un solo consultorio**
- maneja **datos clínicos sensibles**
- prioriza **claridad y control** sobre automatismos
- evita complejidad innecesaria (cloud, SaaS, microservicios)

👉 Copilot debe proponer **soluciones simples, explícitas y seguras**,  
no arquitecturas sobredimensionadas.

---

## 🧭 Próximo paso recomendado

Elegir uno y avanzar sin dispersión:

1️⃣ Diseñar e implementar **sistema de backups**  
2️⃣ Preparar **estructura final + config para packaging**  
3️⃣ Checklist **PyInstaller** paso a paso

Florens está listo para pasar de *proyecto sólido* a *producto entregable*.
