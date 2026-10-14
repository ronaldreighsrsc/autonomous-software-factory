# 🧠 MEMORY.md — Memoria Persistente de autonomous-software-factory

## 📍 1. Estado Actual del Proyecto
- **Fase:** Inicialización Greenfield.
- **Suite Multiagente:** 4 agentes (.agents/) y 10 comandos /sdd-* listos.
- **Próximo Paso:** Crear la primera especificación funcional con `/sdd-spec 001-core-architecture`.

## ⚖️ 2. Decisiones Clave (y por qué)
- **Estructura Clean Architecture:** Se separan `domain/`, `engines/`, `services/` y `connectors/` para garantizar desacoplamiento y testeabilidad.

## ⚠️ 3. Aprendizajes y Trampas a Evitar
- No escribir código de producción sin un test previo que falle en rojo (TDD estricto).
