# Runbooks por Fase SDD (Carga Progresiva — Antigravity)

> Equivalente nativo en **Google Antigravity** de los slash commands `.agents/commands/sdd-*.md` (los cuales siguen activos para OpenCode / Claude Code).  
> En Antigravity, cuando el usuario pida cualquiera de estas fases (ya sea vía `/sdd <fase>`, `/sdd-<fase>` o en lenguaje natural como *"haz la spec"*, *"clarifica la spec"*, *"arma el plan"*, *"implementa T1"*, *"valida la spec"*), ejecuta exactamente el runbook correspondiente usando la skill `sdd` y las checklists de [roles_y_checklists_sdd.md](./roles_y_checklists_sdd.md).

---

## Índice Rápido de Fases

| Fase (equivalente `/sdd-*`) | Propósito | ¿Edita código? | Gate / Salida obligatoria |
| :--- | :--- | :--- | :--- |
| **`constitution`** | Proponer/revisar principios en `docs/constitution.md` | No | Esperar aprobación antes de escribir archivo |
| **`spec`** | Entrevistar ambigüedades y generar `specs/NNN-nombre/spec.md` | No | `Estado: borrador`, solo QUÉ y POR QUÉ en EARS |
| **`clarify`** | QA de solo lectura sobre `spec.md` | No | Lista numerada de hallazgos, sin soluciones |
| **`plan`** | Generar `specs/NNN-nombre/plan.md` tras aprobar spec | No | Vertical Slice + estrategia `py -m pytest` + `T0` si frontera hostil |
| **`tasks`** | Dividir `plan.md` en `specs/NNN-nombre/tasks.md` | No | Máx. 8–10 tareas verticales (`- [ ] **Tn: ...**`) |
| **`implement`** | Ejecutar **1 sola tarea** en Modo Semáforo `/pair` | Sí | 🔴→🟢→🔵 + `[x]` en `tasks.md` + **PARAR** |
| **`validate`** | Auditar `spec.md` RF por RF y guardrails | No | `VEREDICTO: APROBADO` o `CAMBIOS NECESARIOS` |
| **`change`** | Registrar cambio de requisito primero en `spec.md` | No | Diff de `spec.md` + impacto en plan/tasks + esperar aprobación |
| **`status`** | Diagnóstico rápido de avance de una spec | No | Fase actual, `x de y` tareas y siguiente paso exacto |

---

## 1. `constitution` — Proponer Constitución del Proyecto
- **Lectura previa:** `AGENTS.md`, `MEMORY.md` y código principal del proyecto.
- **Acción:** Proponer **6 principios innegociables**, cortos y verificables (máx. 15 líneas en total) que cubran: simplicidad del stack, relación entre spec y código, separación entre lógica e interfaz, política de tests, protección de datos del usuario e idioma del código y los textos.
- **Restricción:** **NO escribir `docs/constitution.md` todavía**; esperar aprobación explícita del usuario.

## 2. `spec` — Entrevistar y Generar `specs/<NNN-nombre>/spec.md`
- **Lectura previa:** `docs/constitution.md` y `MEMORY.md`.
- **Restricción absoluta:** **NO escribir código.** Solo el **QUÉ** y el **POR QUÉ** (nada de stack, arquitectura ni nombres de archivos).
- **Procedimiento:**
  1. Si hay ambigüedades, hacer preguntas de **UNA en UNA** (casos límite, errores, qué queda fuera de esta versión), **máximo 5 preguntas**.
  2. Con las respuestas, crear `specs/<NNN-nombre>/spec.md` usando la plantilla de `SKILL.md` (requisitos en sintaxis **EARS**, historias `HU-x` verticales, `Fuera de alcance` y `"Estado: borrador"`).

## 3. `clarify` — Auditoría QA de `specs/<NNN-nombre>/spec.md`
- **Acción:** Revisar `spec.md` en modo QA de solo lectura y listar de forma numerada:
  1. Ambigüedades restantes (requisitos no verificables).
  2. Contradicciones entre requisitos.
  3. Casos límite no cubiertos.
  4. Conflictos con `docs/constitution.md` (y `AGENTS.md`).
- **Restricción:** **Solo detecta**, no propongas soluciones ni edites código todavía.

## 4. `plan` — Generar `specs/<NNN-nombre>/plan.md`
- **Prerrequisito:** Spec **aprobada** y sin dudas abiertas (`[NECESITA ACLARACIÓN]`). Si no lo está, **para y avisa**.
- **Lectura previa:** `docs/constitution.md`, `AGENTS.md` y `specs/<NNN-nombre>/spec.md`.
- **Restricción absoluta:** **NO escribir código.** Prohibido cortar por capas horizontales o inventar patrones/interfaces *"por si acaso en el futuro"*.
- **Contenido obligatorio de `plan.md`:**
  - Archivos mínimos a crear o modificar y su responsabilidad exacta.
  - Funciones puras de lógica (con `"hoy"` / `current_date` como parámetro inyectado cuando aplique).
  - Algoritmo mínimo en pseudocódigo y cómo se expone en la interfaz (CLI o visual).
  - Decisiones técnicas justificadas (con alternativa descartada).
  - Estrategia de tests paso a paso con `py -m pytest`.
  - Mapeo explícito de qué `RF` cubre cada componente.
  - Si hay acoplamiento a runtime externo hostil (DOM, CSP, API de terceros), incluir `T0: Spike de Validación Empírica en Vivo`.

## 5. `tasks` — Dividir en Tareas Verticales (`specs/<NNN-nombre>/tasks.md`)
- **Entrada:** `specs/<NNN-nombre>/spec.md` y `specs/<NNN-nombre>/plan.md`.
- **Reglas de desglose:**
  - **PROHIBIDO dividir por capas horizontales** (ej. *"1. toda la BD, 2. toda la API, 3. toda la UI"*).
  - Cada tarea debe ser un **Vertical Slice** pequeño (**15–25 min**, **máx. 3 archivos**) verificable de extremo a extremo.
  - Incluir primero `T0: Spike Técnico de Frontera` si aplica frontera externa hostil.
  - Formato con checkboxes (`- [ ] **Tn: ...**`), `RF` asociados y línea `"Hecho cuando:"` verificable.
  - **Máximo 8–10 tareas**; si salen más, proponer dividir la spec en dos slices independientes.

## 6. `implement` — Ejecutar 1 Tarea en Modo Semáforo (`/pair`)
- **Alcance:** Implementar **SOLO la tarea `Tn` indicada** de `specs/<NNN-nombre>/tasks.md`, siguiendo `plan.md`, `docs/constitution.md` y `SKILL.md`.
- **Ciclo obligatorio:**
  1. 🔴 **ROJO:** Escribir primero el test y comprobar que falla por el motivo esperado (prohibido editar/borrar tests existentes para hacer trampa).
  2. 🟢 **VERDE:** Escribir el **código mínimo y más simple posible** hasta que pase (**máx. 3 archivos y ~50–80 líneas**; cero capas futuras).
  3. 🔵 **REFACTOR:** Ejecutar `py -m pytest` (100% en verde) y limpiar duplicación solo si hace falta.
- **Cierre de iteración:** Marcar `[x]` en `tasks.md`, indicar `RF` cubiertos y **PARAR** esperando revisión del Navigator (no iniciar `Tn+1`).

## 7. `validate` — Validación Final RF por RF
- **Procedimiento:**
  1. Recorrer `specs/<NNN-nombre>/spec.md` requisito por requisito (`RF`).
  2. Indicar qué test cubre cada `RF` y el resultado real de correr `py -m pytest`.
  3. Para `RF` de interfaz o conectores web no cubiertos por unit tests, validar ejecutando la CLI o mediante **Chrome DevTools MCP (puerto 9222)**.
  4. Verificar criterios de finalización y los **Guardrails Invariantes** de `AGENTS.md` (ver [roles_y_checklists_sdd.md](./roles_y_checklists_sdd.md)).
- **Restricción:** Si algo falta o falla, reportarlo claramente; **no arreglar nada todavía**.
- **Salida obligatoria:** `VEREDICTO: APROBADO` o `VEREDICTO: CAMBIOS NECESARIOS`.

## 8. `change` — Cambio de Requisito en una Spec Existente
- **Restricción absoluta:** **NO tocar código todavía.**
- **Procedimiento:**
  1. Actualizar `specs/<NNN-nombre>/spec.md`: nuevo `RF` (o ajuste del existente) en EARS, casos límite y fuera de alcance.
  2. Indicar qué partes de `plan.md` y `tasks.md` habría que ajustar después.
  3. Mostrar el diff de la spec y **esperar aprobación**.

## 9. `status` — Estado Actual y Siguiente Paso
- **Acción (solo lectura — sin editar archivos):** Leer `specs/<NNN-nombre>/` (`spec.md`, `plan.md`, `tasks.md`) y `MEMORY.md`, y responder en pocas líneas:
  1. Fase del flujo SDD y estado de la spec.
  2. Tareas completadas y pendientes (`x de y`).
  3. Siguiente paso exacto recomendado.
