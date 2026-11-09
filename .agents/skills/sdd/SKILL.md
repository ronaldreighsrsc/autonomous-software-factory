---
name: sdd
description: "Úsala siempre que trabajes con Spec-Driven Development + Vertical Slices + AI Pair Programming en este proyecto (docs/constitution.md o cualquier archivo dentro de specs/) - redactar, revisar o cambiar specs, planes y tareas, o implementar y validar tareas de una spec."
---

# Spec-Driven Development (SDD) + Vertical Slices & AI Pair Programming

## Flujo de Trabajo
Constitución → Spec (Vertical Slice) → Clarificación → Plan Mínimo → Tareas Verticales → Implementación (`/pair` Semáforo) → Validación → Cambio.
- **Nunca pases a la siguiente fase sin la aprobación explícita del usuario (Navigator).**
- **La spec manda:** Si algo no está en la spec, no se implementa. Si falta una decisión, para y pregunta.
- **No es Cascada (Waterfall):** Prohibido planificar todo un sistema monolítico de una sola vez o inventar capas "para el futuro". Cada spec aborda un **Vertical Slice** acotado.
- Un cambio de requisitos se hace primero en la spec, luego en el plan y las tareas, y por último en el código.
- Cada spec vive en su propia carpeta: `specs/NNN-nombre/` con `spec.md`, `plan.md` y `tasks.md`.
- Al culminar una spec completa, actualiza `MEMORY.md` de forma concisa (<100 líneas, solo decisiones vigentes; prohibido narrar autopsias de bugs).

## ⚖️ Cuándo usar SDD vs. TDD Directo (Cero Desperdicio Lean)
- **Usar SDD Formal (`specs/NNN-...`):** Nuevas capacidades de negocio, nuevos comandos CLI, módulos o subsistemas completos, modificaciones en esquemas de datos o nuevos conectores web.
- **NO usar SDD (Usar TDD Directo):** Corrección de bugs (selectores DOM, escape LaTeX `\&`, typos), afinación de aliases/habilidades en `config.py` o refactorizaciones internas sin cambio de API. Flujo: Test rojo $\rightarrow$ Fix mínimo $\rightarrow$ Verde en <1s.

## 🍰 Regla de Oro 1: Vertical Slices (Prohibido Construir por Capas Horizontales)
- **Qué está PROHIBIDO (Capas Horizontales):** Dividir specs o tareas en *"T1: Crear toda la base de datos/modelos; T2: Crear toda la lógica/API; T3: Crear toda la interfaz/CLI"*. Eso impide probar nada hasta el final y genera miles de líneas sin validar.
- **Qué es OBLIGATORIO (Vertical Slices):** Cada historia de usuario (`HU-x`) y cada tarea (`Tn`) debe ser una **rebanada vertical** que atraviese solo lo mínimo necesario (datos $\rightarrow$ lógica $\rightarrow$ salida/CLI) para entregar **1 comportamiento funcional y verificable de extremo a extremo desde el minuto 1**.
- **Arquitectura Emergente:** Prohibido crear patrones repositorio, factories, interfaces abstractas con una sola implementación o carpetas vacías "por si acaso en el futuro". El diseño emerge al refactorizar sobre tests en verde.

## Plantilla de Especificación (`spec.md`)
```markdown
# Spec NNN — <Nombre del Vertical Slice>
Estado: borrador | aprobada | implementada

## Contexto y objetivo
<Qué problema resuelve y por qué merece la pena. Un párrafo.>

## Usuarios / actores
<Quién lo usa.>

## Historias de usuario (Vertical Slices)
- HU-1: Como <rol>, quiero <acción concreta> para <beneficio medible>. (1 sola responsabilidad por historia)

## Definiciones (solo si hay términos que puedan interpretarse de varias formas)

## Requisitos funcionales (en EARS)
## Requisitos no funcionales
## Casos límite
## Fuera de alcance (Out of Scope estricto para evitar sobreingeniería)
## Criterios de finalización
## Dudas abiertas
- [NECESITA ACLARACIÓN] <duda>
```
*Regla de oro:* La spec describe el **QUÉ** y el **POR QUÉ**. Nada de stack técnico, arquitectura ni nombres de archivos de código.

## Requisitos en EARS (en español)
- **RF-x:** **CUANDO** <evento>, **EL SISTEMA** <respuesta esperada>.
- **RF-x:** **SI** <condición no deseada>, **ENTONCES EL SISTEMA** <respuesta de contingencia>.
- **RF-x:** **MIENTRAS** <estado activo>, **EL SISTEMA** <respuesta continua>.
- **RF-x:** **EL SISTEMA** <comportamiento permanente incondicional>.

*Cada RF debe ser verificable:* Prohibido usar adjetivos vagos como "rápido", "intenso" o "amigable" sin un criterio cuantitativo medible.

## Plan de Implementación (`plan.md`)
Debe ser conciso y sin sobreingeniería:
- Archivos y responsabilidades (solo los estrictamente necesarios para este slice).
- Funciones puras de lógica (con "hoy" / `current_date` como parámetro inyectado cuando aplique).
- Algoritmo mínimo en pseudocódigo.
- Diseño de la interfaz (CLI o visual).
- Decisiones técnicas justificadas con su alternativa descartada.
- Estrategia de pruebas automatizadas con `py -m pytest` (listado de comportamientos a probar uno a uno).
- Mapeo explícito de qué RF cubre cada componente.
- **Mandato de Fronteras Hostiles de Terceros (Spike T0):** Si la arquitectura se acopla a una plataforma ajena (DOM de LinkedIn, SAP ERP, APIs de terceros, CSP/Trusted Types o extensiones), el plan DEBE incluir obligatoriamente una tarea preliminar: `T0: Spike de Validación Empírica en Vivo`. Prohibido asumir que un mock en Pytest garantiza ejecución en runtimes hostiles externos ("La Ilusión del Mocking").

## Tareas (`tasks.md`)
```markdown
- [ ] **T0: Spike Técnico de Frontera (si aplica).** (RF-x)
  - Runtime objetivo: <e.g. DOM vivo de LinkedIn, CSP, API externa>
  - Invariantes a validar: CSP, Trusted Types, sanitizadores, eventos o ciclo de vida.
  - Hecho cuando: Un snippet mínimo ejecutable corre en vivo en el entorno real sin excepciones de seguridad.

- [ ] **Tn: <Descripción breve del Vertical Slice / paso>.** (RF-x, RF-y)
  - Archivos: <máximo 3 rutas>
  - Hecho cuando: <comprobación verificable end-to-end>.
```
Máximo 15-25 min por tarea (máx. 3 archivos por paso), en orden de dependencias. Si salen más de 8-10 tareas, propón dividir la spec.

## 🚦 Regla de Oro 2: Implementación en Modo Semáforo `/pair` (AI Pair Programming)
El humano actúa como **Navigator** (piloto que decide y revisa) y el agente como **Driver** (escribe código en pasos cortos).
Una sola tarea / iteración a la vez (máximo ~50-80 líneas y $\le 3$ archivos por paso):
1. 🔴 **ROJO (Test primero):** Escribe **1 test** claro para el comportamiento actual y verifica que falle por el motivo esperado. **ESTRICTAMENTE PROHIBIDO** modificar o borrar un test existente para forzar que el código pase.
2. 🟢 **VERDE (Código mínimo):** Escribe la **cantidad mínima de código** necesaria para que el test pase. Cero funcionalidades no pedidas, cero abstracciones anticipadas.
3. 🔵 **REFACTOR (Solo en verde):** Si el código creció o hay duplicación real, aplica o propone un refactor manteniendo el 100% de `py -m pytest` en verde.
4. Marcar la tarea completada (`[x]`) en `tasks.md` y **PARAR** para revisión del Navigator (nunca generar PRs monolíticos de miles de líneas sin pausa).
