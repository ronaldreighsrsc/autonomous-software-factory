---
description: "SDD · Valida la spec RF por RF (tests + Chrome DevTools / CLI)"
agent: reviewer
---

Recorre `specs/$1/spec.md` requisito por requisito. Para cada RF indica qué test lo cubre y el resultado de ejecutarlo con `py -m pytest`.

Los RF de interfaz o conectores web que no se puedan testear con pruebas unitarias, verifícalos ejecutando la CLI o mediante el MCP de Chrome DevTools (puerto 9222).

Si algún RF no está cubierto o falla, dilo claramente. **NO arregles nada todavía.**

Después comprueba los criterios de finalización y dame un veredicto explícito:
- `VEREDICTO: APROBADO`
- `VEREDICTO: CAMBIOS NECESARIOS`
