# Tareas de Implementación — SPEC-001: Core Architecture & Closed-Loop Engine

- [x] **Tarea 1: Modelos de Dominio y Esquemas Pydantic v2**
  - Implementar `autonomous_software_factory/domain/models.py` y `events.py`.
  - Crear pruebas unitarias en `tests/test_domain_models.py`.
  - Verificar validación de tipos, serialización y cálculo de invariantes. (COMPLETADO: 4 tests en verde).

- [x] **Tarea 2: Motor de Circuit Breakers y Anti-Oscilación**
  - Implementar `autonomous_software_factory/engines/circuit_breaker.py`.
  - Crear pruebas en `tests/test_circuit_breaker.py` (hashing idéntico consecutivo, límite de $0.25 USD, tope de 8 pasos). (COMPLETADO: 4 tests en verde).

- [x] **Tarea 3: Oráculo Determinista y Motor de Reflexión**
  - Implementar `autonomous_software_factory/engines/oracle.py` y `reflexion.py`.
  - Crear pruebas en `tests/test_oracle.py` (criterio estricto `exit_code == 0`, sanitización de trazas). (COMPLETADO: 3 tests en verde).

- [x] **Tarea 4: Motor de Estados Tipado (StateGraph FSM)**
  - Implementar `autonomous_software_factory/engines/state_engine.py`.
  - Crear pruebas en `tests/test_state_engine.py` (transiciones de lazo cerrado, compuerta humana y fast-path). (COMPLETADO: 6 tests en verde).

- [x] **Tarea 5: Servicio de Checkpointing y Time-Travel (SQLite WAL)**
  - Implementar `autonomous_software_factory/services/checkpoint_service.py`.
  - Crear pruebas en `tests/test_checkpoint_service.py` (persistencia WAL, rollback de estados). (COMPLETADO: 4 tests en verde).

- [x] **Tarea 6: Orquestador de Fábrica y Adaptador Agéntico Antigravity**
  - Implementar `autonomous_software_factory/connectors/agent_worker.py` y `services/orchestrator.py`.
  - Crear pruebas en `tests/test_orchestrator.py` (ejecución en lazo cerrado e integración). (COMPLETADO: 4 tests en verde).

- [x] **Tarea 7: Interfaz CLI y Telemetría AgentOps**
  - Implementar `autonomous_software_factory/cli.py` con comandos `run`, `inspect`, `rollback`, `telemetry`.
  - Crear pruebas en `tests/test_cli.py`. (COMPLETADO: 4 tests en verde en 0.82s).

- [x] **Tarea 8: Portafolio, Catálogo y Documentación**
  - Redactar README.md de clase mundial con diagramas Mermaid y métricas.
  - Registrar el Proyecto #11 en `job_copilot/domain/catalog.py`.
  - Ejecutar suite completa con `py -m pytest tests -q` (100% verde) y subir a GitHub. (COMPLETADO: 29 tests en verde, README.md internacional, catálogo registrado).
