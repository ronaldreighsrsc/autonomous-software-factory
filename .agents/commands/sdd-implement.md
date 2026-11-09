---
description: "SDD /pair · Implementa UNA tarea en Modo Semáforo (Rojo -> Verde -> Refactor) (uso: /sdd-implement 001-slice T1)"
agent: implementer
---

Implementa **SOLO** la tarea $2 de `specs/$1/tasks.md` en **Modo Semáforo (`/pair`)**, siguiendo `specs/$1/plan.md`, `docs/constitution.md` y la skill `sdd`:

1. 🔴 **ROJO:** Escribe primero el test del comportamiento y comprueba que falla por el motivo esperado. Prohibido modificar o borrar tests existentes para hacer trampa.
2. 🟢 **VERDE:** Escribe el **código mínimo y más simple posible** hasta que el test pase (máx. 3 archivos y ~50-80 líneas; cero capas o funciones "para el futuro").
3. 🔵 **REFACTOR:** Ejecuta `py -m pytest` (100% en verde) y limpia duplicación solo si es necesario.
4. Marca la tarea $2 como hecha (`[x]`) en `specs/$1/tasks.md` e indica qué RF cubre.

**Después PÁRATE y espera la revisión del Navigator (usuario). No empieces la siguiente tarea.**
