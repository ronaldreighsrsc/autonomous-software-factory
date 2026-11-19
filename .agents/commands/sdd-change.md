---
description: "SDD · Nuevo requisito: primero la spec, luego el código"
agent: planner
---

<!-- [Multi-herramienta] Activo para OpenCode / Claude Code (slash command /sdd-*). No eliminar ni borrar frontmatter. En Google Antigravity, los runbooks equivalentes con carga progresiva viven en .agents/skills/sdd/references/runbooks_fases_sdd.md -->

Nuevo requisito para la spec `specs/$1/` (el texto que va después del nombre de la carpeta): $ARGUMENTS

**NO toques código.** Usa la skill `sdd`.

1. Actualiza `specs/$1/spec.md`: nuevo RF (o cambio de uno existente) en EARS, sus casos límite y lo que queda fuera de alcance.
2. Indica qué partes de `plan.md` y `tasks.md` habría que cambiar después.
3. Muéstrame el diff de la spec y espera mi aprobación.
