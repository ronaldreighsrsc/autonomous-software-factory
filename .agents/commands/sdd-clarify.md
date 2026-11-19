---
description: "SDD · Revisa la spec como un QA (solo detecta, no resuelve)"
agent: reviewer
---

<!-- [Multi-herramienta] Activo para OpenCode / Claude Code (slash command /sdd-*). No eliminar ni borrar frontmatter. En Google Antigravity, los runbooks equivalentes con carga progresiva viven en .agents/skills/sdd/references/runbooks_fases_sdd.md -->

Revisa `specs/$1/spec.md` como si fueras un QA muy profesional. Usa la skill `sdd`.

Lista:
1. Ambigüedades restantes (requisitos que no se pueden verificar).
2. Contradicciones entre requisitos.
3. Casos límite no cubiertos.
4. Conflictos con `docs/constitution.md`.

No propongas soluciones todavía: solo detecta. Formato: lista numerada.
