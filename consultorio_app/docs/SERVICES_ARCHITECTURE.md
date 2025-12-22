# 🧠 Refactoring Guideline — Services Architecture (OdontoApp)

Este documento define **cómo deben refactorizarse y diseñarse los services** del backend de OdontoApp para lograr un estándar de calidad profesional, alta modularidad y preparación para futuras integraciones (API, WhatsApp, scheduler, deploy web o desktop).

El objetivo principal es pasar de **services basados en entidades** a **services basados en casos de uso (use cases)**.

---

## 🎯 Objetivo del refactor

* Mejorar la separación de responsabilidades
* Reducir la lógica de negocio en routes
* Facilitar testing y mantenimiento
* Preparar el backend para múltiples puntos de entrada
* Evitar acoplamientos innecesarios con Flask o HTTP

---

## 🏗️ Principios arquitectónicos

### 1. Services = Casos de uso (Use Cases)

Los services **NO representan entidades**, sino **acciones del sistema**.

❌ Patrón a evitar:

```text
PacienteService
TurnoService (CRUD genérico)
```

✅ Patrón deseado:

```text
CrearPacienteService
AgendarTurnoService
CambiarEstadoTurnoService
MarcarTurnosVencidosService
```

Cada service:

* Implementa **un único caso de uso**
* Coordina uno o más modelos del dominio
* Encapsula reglas de negocio

---

### 2. Organización por dominio + acción

Los services se agrupan por **dominio funcional**, no por capa técnica.

```text
services/
├── paciente/
│   ├── CrearPacienteService.py
│   ├── EditarPacienteService.py
│   └── BuscarPacienteService.py
│
├── turno/
│   ├── AgendarTurnoService.py
│   ├── CambiarEstadoTurnoService.py
│   ├── MarcarTurnosVencidosService.py
│   └── CancelarTurnoService.py
│
├── conversacion/        # futura integración WhatsApp
│   └── ProcesarMensajeService.py
│
└── common/
    ├── exceptions.py
    └── validators.py
```

---

## ⚙️ Responsabilidades de un Service

### Un service **DEBE**:

* Recibir datos primitivos (ids, strings, fechas)
* Validar reglas de negocio
* Operar sobre modelos del dominio
* Manejar persistencia (commit / rollback)
* Devolver un resultado claro **o** lanzar una excepción de negocio

### Un service **NO DEBE**:

* Importar Flask
* Usar `request`, `session`, `flash`, `redirect`
* Renderizar templates
* Conocer detalles de HTTP, UI o frontend

---

## 🧩 Convención de interfaz de services

Cada service expone **un único punto de entrada**:

```python
class AgendarTurnoService:
    @staticmethod
    def execute(...):
        ...
```

Esto permite que el mismo service sea utilizado por:

* routes HTML
* endpoints de API JSON
* tareas programadas (scheduler)
* integraciones externas (WhatsApp)

---

## 🚨 Excepciones de negocio

Las violaciones de reglas de negocio se representan mediante **excepciones propias**.

```python
class TurnoInvalidoError(Exception):
    pass
```

* Los services **lanzan** excepciones
* Las routes **las capturan** y deciden cómo responder

Esto mantiene la lógica de negocio separada de la UI.

---

## 🔄 Manejo de transacciones

Los services son dueños del límite transaccional:

* Ejecutan `commit()` si el caso de uso finaliza correctamente
* Ejecutan `rollback()` ante cualquier error

Las routes **NO deben** manejar transacciones.

---

## 🔌 Rol de las Routes (Adapters)

Las routes funcionan como **adaptadores** entre HTTP y el dominio.

Responsabilidades de una route:

* Obtener datos desde HTTP (form, JSON, params)
* Llamar al service correspondiente
* Manejar respuestas (HTML, JSON, mensajes)

Las routes **NO contienen reglas de negocio**.

---

## 🌐 Preparación para integraciones futuras (WhatsApp)

Los services deben diseñarse asumiendo que **no siempre serán llamados desde HTTP**.

Buenas prácticas:

* No depender de Flask
* Recibir un parámetro `origen` o `canal` (WEB / API / WHATSAPP)
* Comportamiento determinista basado solo en inputs

Esto permite integrar WhatsApp como **un adaptador externo**, sin modificar la lógica central.

---

## 📌 Resumen clave

* Los services implementan **casos de uso**, no CRUDs genéricos
* Cada service hace **una sola cosa**
* Las routes son delgadas y sin lógica
* La lógica vive en services
* El diseño queda preparado para crecer sin romperse

> **Key guideline:** Services implement business use cases and must remain independent from routes, UI, and transport layers.

---

Este documento debe usarse como referencia obligatoria durante el refactor y como contexto para herramientas como GitHub Copilot.
