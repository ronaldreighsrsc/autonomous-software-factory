---
description: "SDD · Genera el plan técnico de una spec aprobada"
agent: planner
---

Lee `docs/constitution.md`, `AGENTS.md` y `specs/$1/spec.md`. Usa la skill `sdd`.

NO escribas código.

Genera `specs/$1/plan.md` con:
- Archivos que se crean o modifican y la responsabilidad de cada uno.
- Funciones puras de lógica (con "hoy" / `current_date` como parámetro inyectado).
- Algoritmo en pseudocódigo.
- Cómo se pinta en la interfaz.
- Decisiones técnicas justificadas (con su alternativa descartada).
- Estrategia de tests con `py -m pytest`.

Todo debe respetar la constitución y cubrir todos los RF. Marca qué RF cubre cada parte.
Si la spec no está aprobada o tiene dudas abiertas, para y avísame.
