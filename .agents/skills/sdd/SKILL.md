---
name: sdd
description: "Úsala siempre que trabajes con Spec-Driven Development en este proyecto (docs/constitution.md o cualquier archivo dentro de specs/) - redactar, revisar o cambiar specs, planes y tareas, o implementar y validar tareas de una spec."
---

# Spec-Driven Development (SDD)

## Flujo de Trabajo
Constitución → Spec → Clarificación → Plan → Tareas → Implementación → Validación → Cambio.
- **Nunca pases a la siguiente fase sin la aprobación explícita del usuario.**
- **La spec manda:** Si algo no está en la spec, no se implementa. Si falta una decisión, para y pregunta.
- Un cambio de requisitos se hace primero en la spec, luego en el plan y las tareas, y por último en el código.
- Cada spec vive en su propia carpeta: `specs/NNN-nombre/` con `spec.md`, `plan.md` y `tasks.md`.
- Al terminar cada fase o hito, actualiza `MEMORY.md`.

## ⚖️ Cuándo usar SDD vs. TDD Directo (Cero Desperdicio Lean)
- **Usar SDD Formal (`specs/NNN-...`):** Nuevas capacidades de negocio, nuevos comandos CLI, módulos o subsistemas completos, modificaciones en esquemas de datos o nuevos conectores web.
- **NO usar SDD (Usar TDD Directo):** Corrección de bugs (selectores DOM, escape LaTeX `\&`, typos), afinación de aliases/habilidades en `config.py` o refactorizaciones internas sin cambio de API. Flujo: Test rojo $\rightarrow$ Fix $\rightarrow$ Verde en <1s.

## Plantilla de Especificación (`spec.md`)
```markdown
# Spec NNN — <Nombre>
Estado: borrador | aprobada | implementada

## Contexto y objetivo
<Qué problema resuelve y por qué merece la pena. Un párrafo.>

## Usuarios / actores
<Quién lo usa.>

## Historias de usuario
- HU-1: Como <rol>, quiero <acción> para <beneficio>.

## Definiciones (solo si hay términos que puedan interpretarse de varias formas)

## Requisitos funcionales (en EARS)
## Requisitos no funcionales
## Casos límite
## Fuera de alcance
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
Debe estructurarse en:
- Archivos y responsabilidades.
- Funciones puras de lógica (con "hoy" / `current_date` como parámetro inyectado).
- Algoritmo en pseudocódigo.
- Diseño de la interfaz (CLI o visual).
- Decisiones técnicas justificadas con su alternativa descartada.
- Estrategia de pruebas automatizadas con `py -m pytest`.
- Mapeo explícito de qué RF cubre cada componente.

## Tareas (`tasks.md`)
```markdown
- [ ] **Tn: <Descripción breve>.** (RF-x, RF-y)
  - Archivos: <rutas>
  - Hecho cuando: <comprobación verificable>.
```
Máximo 20-30 min por tarea, en orden estricto de dependencias. Si salen más de 10 tareas, propón dividir la spec.

## Implementación
Una sola tarea a la vez:
1. Tests primero (en rojo).
2. Código que hace pasar los tests.
3. Ejecución de `py -m pytest` (100% en verde).
4. Marcar la tarea completada (`[x]`) en `tasks.md` y **parar**.
