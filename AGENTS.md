# 🤖 AGENTS.md — Reglas y Guardrails de autonomous-software-factory

## 🛠️ Stack y Verificación
- **Stack:** Python 3.12+, Clean Architecture, Pytest.
- **Tests (mandatorio en verde):** `py -m pytest tests -q`

## ⚖️ Protocolo Autónomo de Enrutamiento: TDD Directo vs. SDD Formal
- **Fast-Path en Terminal y Git (<5s / Cero Fricción):** Comandos explícitos de terminal (`git add`, `git commit -m "..."`, ejecución de scripts). Ejecución inmediata sin auditorías de seguridad no solicitadas, sin arqueología forense ni modales `ask_question`.
- **TDD Directo (Cero Desperdicio / *Muda*):** Bugfixes, regex, selectores, afinación de constantes o refactors internos. Flujo: Test en rojo $\rightarrow$ Fix $\rightarrow$ Pytest en verde (<1s). Sin sobrecarga documental en `specs/`.
- **SDD Formal (Arquitectura y Nuevas Capacidades):** Nuevos módulos, subsistemas, cambios en contratos o esquemas de datos. Flujo: `specs/NNN-nombre/` (`spec.md` EARS $\rightarrow$ `plan.md` $\rightarrow$ `tasks.md`) con aprobación previa.
- **Autonomía:** El asistente clasifica y ejecuta automáticamente el protocolo adecuado sin que el usuario tenga que solicitarlo.

## 🛑 Límites y Guardrails Operativos
- 🚫 **NUNCA:**
  - **Over-Engineering Burocrático:** Jamás convertir una orden operativa directa en una ceremonia de auditoría, lectura de 100 líneas irrelevantes o encuesta interactiva.
  - Crear scripts sueltos en la raíz; todo desarrollo vive en `autonomous-software-factory/`.
  - Implementar lógica no aprobada en la spec activa.
  - Alucinar librerías externas o modificar esquemas sin autorización.
- ⚠️ **PREGUNTA ANTES:**
  - Cambios mayores en la arquitectura o interfaces públicas.
- ✅ **SIEMPRE:**
  - Flujo SDD estricto cuando aplique: Spec ➔ Plan ➔ Tasks ➔ TDD ➔ Validación.
  - Actualizar `MEMORY.md` al culminar hitos significativos.
  - Mantener todos los tests en verde antes de dar por cerrada cualquier tarea.
