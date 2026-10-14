# Plan de Implementación — SPEC-001: Core Architecture & Closed-Loop Engine

## 1. Arquitectura del Sistema (Clean Architecture)

```
autonomous_software_factory/
├── domain/
│   ├── __init__.py
│   ├── models.py            # Pydantic v2 schemas: Task, StatePhase, OracleResult, Budget, ActionHash
│   └── events.py            # Domain events: StateTransitionEvent, CircuitBreakerTrippedEvent
├── engines/
│   ├── __init__.py
│   ├── circuit_breaker.py   # Hashing de acciones, limitador de pasos, presupuestos USD
│   ├── oracle.py            # Oráculo determinista externo para pytest / ruff / mypy
│   ├── reflexion.py         # Sanitización de stacktrace, extracción de diffs y prompts de feedback
│   └── state_engine.py      # StateGraph / FSM tipada con guardas de transición
├── services/
│   ├── __init__.py
│   ├── checkpoint_service.py # SQLite WAL persistence, snapshots y time-travel rollback
│   └── orchestrator.py      # Coordinador en lazo cerrado (Fast-path vs 4-Agent Pipeline)
├── connectors/
│   ├── __init__.py
│   ├── agent_worker.py      # Adapter agéntico para Antigravity SDK con interceptor de seguridad
│   └── mcp_client.py        # Interfaz de herramientas Model Context Protocol (MCP)
└── cli.py                   # CLI interactivo Typer + Rich
```

---

## 2. Contratos de Datos (Pydantic v2)

### StatePhase
`TRIAGE_SPEC` -> `HUMAN_GATE` -> `PLANNER` -> `CODER_TDD` -> `CODE_REVIEWER` -> `ARTIFACT_PUBLISHER` -> `COMPLETED` / `ABORTED`

### CircuitBreaker
- `ActionHash = SHA256(tool_name + canonical_json_args)`
- `oscillation_limit = 2` (segunda llamada idéntica consecutiva = Disparo)
- `max_steps = 8`
- `max_cost_usd = 0.25`

### OracleResult
- `exit_code: int`
- `stdout: str`, `stderr: str`
- `passed: int`, `failed: int`
- `is_success: bool = (exit_code == 0)`

---

## 3. Estrategia de Pruebas (TDD)
1. `tests/test_domain_models.py`: Validación de esquemas Pydantic y serialización.
2. `tests/test_circuit_breaker.py`: Pruebas de anti-oscilación, superación de presupuesto y pasos máximos.
3. `tests/test_oracle.py`: Pruebas del oráculo con salidas simuladas y ejecuciones reales.
4. `tests/test_state_engine.py`: Transiciones válidas e inválidas en la FSM.
5. `tests/test_checkpoint_service.py`: Escritura SQLite WAL y time-travel rollback.
6. `tests/test_orchestrator.py`: Flujo end-to-end de lazo cerrado completo y fast-path.
