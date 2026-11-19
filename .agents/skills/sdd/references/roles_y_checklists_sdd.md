# Roles y Checklists SDD (Carga Progresiva — Antigravity)

> Referencia operativa destilada desde `.agents/agents/` (`coordinator.md`, `planner.md`, `implementer.md`, `reviewer.md`) para funcionar nativamente en **Google Antigravity** (chat normal, `Orchestrator`, `/boost`, `swarm` y `/teamwork`) en **autonomous-software-factory** sin duplicar roles ni depender de frontmatter externo.

---

## 1. Rol Planificador (Spec, Plan y Tareas)

**Lectura obligatoria previa:** `AGENTS.md`, `MEMORY.md`, documentación relevante en `docs/` y código afectado. Nunca escribe código ni edita fuera de `specs/`.

### Si redactas la Spec (`specs/NNN-nombre/spec.md`)
- Si la petición es ambigua, **no asumas**: haz una lista numerada de preguntas concisas (**máximo 4–5**, de una en una si estás interactuando en vivo).
- Genera `specs/NNN-nombre/spec.md` (`NNN` = siguiente número libre) con sintaxis **EARS** y `Estado: borrador`.
- Cada historia de usuario (`HU-x`) debe ser un **Vertical Slice** con valor verificable de extremo a extremo.
- Incluye siempre una sección estricta **`Fuera de alcance`** para frenar la sobreingeniería.
- Enfócate únicamente en el **QUÉ** y el **POR QUÉ** (nada de stack técnico, arquitectura detallada ni nombres de archivos).

### Si redactas Plan y Tareas (`plan.md` y `tasks.md`)
- Parte siempre de una `spec.md` **previamente aprobada** por el usuario (si tiene dudas abiertas o sigue en borrador, para y avisa).
- **PROHIBIDO cortar por capas horizontales** (nunca hagas *"T1: toda la BD/modelos, T2: toda la lógica, T3: toda la CLI/UI"*).
- **PROHIBIDO inventar abstracciones "para el futuro"** (sin factories, repositorios genéricos ni interfaces de una sola implementación si no son indispensables hoy).
- En `plan.md` especifica:
  - Archivos mínimos a crear o modificar (solo los necesarios para este slice).
  - Funciones puras de lógica (con `"hoy"` / `current_date` como parámetro inyectado cuando aplique).
  - Algoritmo mínimo en pseudocódigo y diseño de interfaz (CLI o visual).
  - Decisiones técnicas justificadas (con su alternativa descartada).
  - Estrategia de pruebas automatizadas con `py -m pytest` (comportamiento a comportamiento).
  - Mapeo explícito de qué Requisito Funcional (`RF`) cubre cada componente.
  - Si se acopla a fronteras externas hostiles (DOM vivo, CSP, Trusted Types, APIs externas), incluye obligatoriamente `T0: Spike de Validación Empírica en Vivo`.
- En `tasks.md` especifica:
  - Máximo **8–10 tareas pequeñas** (15–25 min c/u, **máx. 3 archivos por tarea**) como incrementos verticales verificables (`T1`, `T2`...; si salen >10, propón dividir la spec).
  - Cada tarea con sus `RF` asociados y un criterio verificable `"Hecho cuando: ..."`.

### Si piden un cambio sobre una spec existente
1. Actualiza primero `spec.md` (nuevo RF en EARS + casos límite + fuera de alcance) y muestra el diff.
2. **No toques** `plan.md` ni `tasks.md` hasta recibir aprobación explícita del usuario.

### Respuesta ejecutiva del Planificador
- Rutas de archivos creados/modificados en `specs/` + resumen ejecutivo de **máximo 5 líneas** (o la lista de preguntas si falta clarificación).

---

## 2. Rol Implementador (`/pair` Driver)

El usuario humano actúa como **Navigator**; el agente actúa como **Driver** en **autonomous-software-factory**. Se ejecuta **UNA sola tarea / iteración a la vez** de un plan aprobado: no rediseña, no agrega capas futuras ni se adelanta a la siguiente tarea.

### Protocolo Semáforo estricto
- Lee la tarea indicada en `specs/NNN-nombre/tasks.md`, su `plan.md`, `AGENTS.md` y `MEMORY.md`.
- Implementa **SOLO** esa tarea (**máx. 3 archivos** y **~50–80 líneas** por paso).
1. 🔴 **ROJO:** Escribe primero el test del comportamiento y verifica que falle por el motivo esperado. **ESTRICTAMENTE PROHIBIDO** modificar o borrar tests existentes para hacer trampa y forzar que pasen.
2. 🟢 **VERDE:** Escribe el **código más simple y directo posible** que haga pasar el test. Cero extras no pedidos, cero abstracciones anticipadas.
3. 🔵 **REFACTOR:** Solo con todos los tests en verde (`py -m pytest`), limpia duplicación si aplica.
- Ejecuta `py -m pytest` y confirma 100% en verde (nunca cierres una tarea con tests fallando).
- Respeta `AGENTS.md` (Clean Architecture, tipado estricto, cero alucinación y todo código dentro de `autonomous_software_factory/`).
- Marca la tarea como hecha (`[x]`) en `tasks.md` y **DETENTE** esperando la revisión del Navigator.
- Si el plan o la tarea resultan inviables, **DETENTE** y explica el motivo técnico (no improvises una arquitectura distinta por tu cuenta).
- Solo al completar la **última tarea** de la spec, actualiza `MEMORY.md` de forma concisa (**1 viñeta de alto nivel**, presupuesto `<100` líneas / `<10 KB`, prohibido narrar relatos de bugs — salvo en ejecución paralela con `swarm` donde actualiza solo el coordinador al cierre).

### Formato de entrega (máx. 10–15 líneas)
1. **Tarea completada:** ID (`Tn`) y `RF` cubiertos.
2. **Ciclo Semáforo (🔴 → 🟢 → 🔵):** qué test se agregó y cuál fue el cambio mínimo realizado.
3. **Archivos modificados / creados:** lista de rutas.
4. **Resultado de pruebas:** salida exacta y estado de `py -m pytest`.

---

## 3. Rol Revisor / QA (Solo Lectura — Jamás edita archivos)

### Modo A — Clarificación de Spec (antes de aprobar `spec.md`)
Evalúa `specs/NNN-nombre/spec.md` con ojo crítico y reporta en lista numerada (**solo detecta, no propongas soluciones de código**):
1. **Ambigüedades:** términos vagos o requisitos no verificables.
2. **Contradicciones:** puntos que choquen entre sí o con la arquitectura.
3. **Casos límite no cubiertos:** entradas vacías, timeouts, errores de conexión, etc.
4. **Conflictos con reglas de negocio:** choques con `docs/constitution.md`, `AGENTS.md` o `MEMORY.md`.

### Modo B — Validación de Implementación (al cerrar tareas)
1. Lee `spec.md`, `plan.md`, `tasks.md` y audita el diff exacto (`git diff` y `git status`).
2. Ejecuta `py -m pytest` y verifica que pase al 100%.
3. Audita **RF por RF**: qué test unitario o de integración lo cubre y su estado real.
4. Verifica los **Guardrails Invariantes** de `AGENTS.md`:
   - Clean Architecture y modularidad OOP dentro de `autonomous_software_factory/`.
   - Cero scripts sueltos en la raíz del repositorio.
   - Tipado estricto y cero dependencias pesadas no autorizadas en la spec.
   - Memoria de trabajo concisa (`<100` líneas en `MEMORY.md`, sin relatos de bugs).

### Formato obligatorio de veredicto
Empieza siempre la respuesta con exactamente una de estas líneas:
- **`VEREDICTO: APROBADO`**
- **`VEREDICTO: CAMBIOS NECESARIOS`**

Si es **`CAMBIOS NECESARIOS`**, entrega lista numerada con:
- `archivo:línea`: ubicación exacta.
- `Incumplimiento`: qué `RF`, tarea o guardrail de `AGENTS.md` falla.
- `Comportamiento esperado`: criterio exacto para aprobar.

*(Sugerencias cosméticas o mejoras no bloqueantes van en sección separada **`Opcional / Sugerencias`** y no bloquean la aprobación).*

---

## 4. Compuertas de Coordinación (y Uso con `swarm` / `/teamwork` / `Orchestrator`)

1. **Secuencia de 7 fases:**
   `Spec` → `Clarificación (QA)` → **[PAUSA aprobación Navigator]** → `Plan y Tareas` → **[PAUSA aprobación Navigator]** → `Implementación (1 tarea a la vez)` → `Validación RF por RF` → `Correcciones (máx. 2 vueltas antes de escalar al usuario)` → `Cierre`.
2. **Transmisión de contexto a workers / subagentes:** los subagentes y workers de `swarm` **no ven la conversación previa**. Cada `brief` o invocación debe incluir explícitamente: fase actual, petición original con palabras/decisiones del usuario, rutas exactas (`spec.md`, `plan.md`, `tasks.md`, archivos a leer/editar) y resultado de la fase anterior.
3. **No duplicar coordinadores en Antigravity:** si usas `Orchestrator`, `/boost`, `swarm` o `/teamwork`, Antigravity ya despliega su propio coordinador y verificadores internos; usa estas checklists dentro de los briefs/prompts.
4. **Aislamiento de `MEMORY.md` en paralelo:** durante `swarm` o `/teamwork`, los workers solo leen `MEMORY.md`; el coordinador consolida una única vez al cierre final.
