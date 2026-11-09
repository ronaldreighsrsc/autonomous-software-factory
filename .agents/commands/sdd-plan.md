---
description: "SDD · Genera el plan técnico mínimo de una spec aprobada (Vertical Slice, cero sobreingeniería)"
agent: planner
---

Lee `docs/constitution.md`, `AGENTS.md` y `specs/$1/spec.md`. Usa la skill `sdd`.

NO escribas código.

Genera `specs/$1/plan.md` respetando **Vertical Slices** y **Arquitectura Emergente**:
- **Prohibido cortar por capas horizontales** o inventar patrones/interfaces "por si acaso en el futuro".
- Archivos mínimos que se crean o modifican y la responsabilidad de cada uno.
- Funciones puras de lógica (con "hoy" / `current_date` como parámetro inyectado cuando aplique).
- Algoritmo mínimo en pseudocódigo.
- Cómo se expone en la interfaz (CLI o visual).
- Decisiones técnicas justificadas (con su alternativa descartada).
- Estrategia de tests paso a paso con `py -m pytest`.
- Si se acopla a un runtime externo hostil (DOM, CSP, API de terceros), incluye `T0: Spike de Validación Empírica en Vivo`.

Todo debe respetar la constitución y cubrir todos los RF. Marca qué RF cubre cada parte.
Si la spec no está aprobada o tiene dudas abiertas, para y avísame.
