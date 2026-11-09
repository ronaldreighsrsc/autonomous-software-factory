# 🧠 MEMORY.md — Memoria Persistente de autonomous-software-factory

## 📍 1. Estado Actual del Proyecto
- **Fase:** Producción v1.0 (`31 passed` en `pytest`, 100% en verde).
- **Suite Multiagente:** 4 agentes (`.agents/`) y comandos SDD actualizados a **Vertical Slice SDD + Modo Semáforo `/pair`**.
- **Specs Completadas:** `specs/001-core-architecture/` (100% implementada y verificada).

## ⚖️ 2. Decisiones Arquitectónicas Activas
- **Clean Architecture & Pydantic v2:** Separación estricta en `domain/`, `engines/`, `services/` y `connectors/` con contratos inmutables.
- **5-Guard Circuit Breaker (Las 3 Alarmas del Navigator):**
  1. *Anti-Loop:* `TRIPPED_OSCILLATION` (hash `SHA-256` de llamadas consecutivas idénticas), `TRIPPED_STEPS` ($\le 8$ pasos) y `TRIPPED_COST` ($\le \$0.25\text{ USD}$).
  2. *Anti-Trampa (`TRIPPED_TEST_TAMPERING`):* Bloqueo criptográfico `SHA-256` de archivos en `tests/` durante la Fase Verde para impedir que el agente altere o elimine tests.
  3. *Vertical Slice Blast-Radius (`TRIPPED_BLAST_RADIUS`):* Límite estricto por paso ($\le 3$ archivos y $\le 100$ líneas de diff) para evitar volcados monolíticos.
- **Checkpointing Transaccional:** Persistencia de estados en `SQLite WAL` (`PRAGMA journal_mode=WAL`) con soporte para *Time-Travel Debugging* y rollbacks deterministas.

## ⚠️ 3. Reglas No Obvias y Guardrails
- Ningún nodo de código se da por válido por afirmación verbal del LLM; solo `exit_code == 0` del `PytestOracle` autoriza la transición.
- Prohibido modificar tests existentes durante la fase de arreglo (el `CircuitBreaker` dispara `TRIPPED_TEST_TAMPERING`).
