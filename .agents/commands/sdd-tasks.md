---
description: "SDD · Divide el plan en tareas verticales pequeñas y verificables"
agent: planner
---

A partir de `specs/$1/spec.md` y `specs/$1/plan.md`, genera `specs/$1/tasks.md` siguiendo el formato de la skill `sdd`:
- **PROHIBIDO dividir por capas horizontales** (ej. "1. toda la base de datos, 2. toda la API, 3. toda la UI").
- Cada tarea debe ser un incremento / **Vertical Slice** pequeño (máx. 15-25 min y máx. 3 archivos cada una), verificable de extremo a extremo.
- Si aplica frontera externa hostil, incluye primero `T0: Spike Técnico de Frontera`.
- Cada tarea con los RF que cubre y una línea `"Hecho cuando:"` verificable.
- Formato con checkboxes (`- [ ] **Tn: ...**`).
- Máximo 8-10 tareas: si salen más, propón dividir la spec en dos slices independientes.
