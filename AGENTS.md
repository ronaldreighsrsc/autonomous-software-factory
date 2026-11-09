# 🤖 AGENTS.md — Reglas y Guardrails de autonomous-software-factory

## 🛠️ Stack y Verificación
- **Stack:** Python 3.12+, Clean Architecture Emergente, Pytest.
- **Tests (mandatorio en verde):** `py -m pytest tests -q`

## 🧠 Protocolo de Memoria Estándar (Anti-Bloat / Presupuesto <100 Líneas)
- **Git y Pytest son la Memoria Histórica:** Git (`git log`) y la suite de tests (`pytest`) son la única fuente histórica de bugs y resoluciones. ESTRICTAMENTE PROHIBIDO redactar relatos de bugs, autopsias o historias de sesiones en `MEMORY.md`.
- **Presupuesto Estricto (<100 Líneas / <10 KB):** `MEMORY.md` es exclusivamente memoria de trabajo caliente de alta densidad. Si entra una nueva decisión, se condensa o poda lo anterior para nunca superar las 100 líneas.
- **Contenido Autorizado en `MEMORY.md`:** 1) Estado activo y tareas en vuelo. 2) Decisiones arquitectónicas activas (1 viñeta concisa por hito). 3) Trampas y reglas no obvias.
- **Aislamiento en Concurrencia (Anti-Race Condition):** Si trabajan dos agentes en paralelo (`agy` en terminal + IDE), la memoria activa en vuelo vive en `specs/NNN-*/tasks.md`. PROHIBIDO que múltiples agentes editen concurrentemente `MEMORY.md` raíz. La consolidación global se realiza al cierre formal de la tarea.
- **Git Worktrees para Paralelismo Real:** Para ejecutar dos agentes simultáneamente en distintas specs, usar ramas desacopladas con `git worktree add ../<carpeta> -b <rama>` para prevenir torn writes y colisiones de disco.

## ⚖️ Protocolo Autónomo de Enrutamiento: TDD Directo vs. Vertical Slice SDD + `/pair`
- **Fast-Path en Terminal y Git (<5s / Cero Fricción):** Comandos explícitos de terminal (`git add`, `git commit -m "..."`, ejecución de scripts). Ejecución inmediata sin auditorías de seguridad no solicitadas, sin arqueología forense ni modales `ask_question`.
- **TDD Directo (Cero Desperdicio / *Muda*):** Bugfixes, regex, selectores, afinación de constantes o refactors internos. Flujo: Test en rojo $\rightarrow$ Fix mínimo $\rightarrow$ Pytest en verde (<1s). Sin sobrecarga documental en `specs/`.
- **Vertical Slice SDD + Modo Semáforo `/pair` (Nuevas Capacidades):** Nuevos módulos, subsistemas, cambios en contratos o esquemas de datos.
  - **Vertical Slices (Prohibido cortar por capas horizontales):** Nunca dividir un proyecto en *"1. Base de datos, 2. Lógica, 3. UI"*. Cada spec (`specs/NNN-slice/`) y cada tarea debe atravesar el sistema de punta a punta entregando valor funcional verificable desde el minuto 1.
  - **Modo Semáforo `/pair` (Driver/Navigator):** El usuario es el *Navigator* y el agente es el *Driver*. Avanzar en pasos pequeños (máx. 3 archivos y ~50-80 líneas por iteración): 🔴 1 Test en Rojo $\rightarrow$ 🟢 Código mínimo para Verde $\rightarrow$ 🔵 Refactor sobre verde. Prohibido crear abstracciones "para el futuro" o modificar tests existentes para hacer trampa.
- **Autonomía:** El asistente clasifica y ejecuta automáticamente el protocolo adecuado sin que el usuario tenga que solicitarlo.

## 🛑 Límites y Guardrails Operativos
- 🚫 **NUNCA:**
  - **Over-Engineering Burocrático ni Cascada:** Jamás convertir una orden operativa directa en una ceremonia de auditoría, ni escupir PRs monolíticos de miles de líneas con patrones factory/repository vacíos "por si acaso".
  - Crear scripts sueltos en la raíz; todo desarrollo vive en `autonomous_software_factory/`.
  - Implementar lógica no aprobada en la spec activa o tocar tests existentes para forzar que pasen.
  - Alucinar librerías externas o modificar esquemas sin autorización.
  - Convertir `MEMORY.md` en un diario de bugs o un changelog.
- ⚠️ **PREGUNTA ANTES:**
  - Cambios mayores en la arquitectura o interfaces públicas.
- ✅ **SIEMPRE:**
  - Flujo Vertical Slice SDD cuando aplique: Spec ➔ Plan Mínimo ➔ Tasks Verticales ➔ `/pair` TDD (Rojo-Verde-Refactor) ➔ Validación.
  - Actualizar `MEMORY.md` de forma concisa (<100 líneas) solo al culminar specs completas, sin narrar bugs resueltos.
  - Mantener todos los tests en verde antes de dar por cerrada cualquier tarea.
