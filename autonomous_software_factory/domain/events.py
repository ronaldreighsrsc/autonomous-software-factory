import time
from typing import Any
from pydantic import BaseModel, Field
from autonomous_software_factory.domain.models import CircuitStatus, StatePhase


class DomainEvent(BaseModel):
    event_id: str
    task_id: str
    timestamp: float = Field(default_factory=time.time)
    payload: dict[str, Any] = Field(default_factory=dict)


class StateTransitionEvent(DomainEvent):
    from_phase: StatePhase
    to_phase: StatePhase
    reason: str = ""


class CircuitBreakerTrippedEvent(DomainEvent):
    status: CircuitStatus
    trigger_reason: str
    action_hash: str | None = None
    step_count: int = 0
    total_cost_usd: float = 0.0


class OracleEvaluatedEvent(DomainEvent):
    exit_code: int
    is_success: bool
    duration_seconds: float
    passed_tests: int
    failed_tests: int
