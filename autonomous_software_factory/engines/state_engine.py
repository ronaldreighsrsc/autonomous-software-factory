import uuid
from typing import Any
from autonomous_software_factory.domain.models import (
    CircuitStatus,
    OracleResult,
    StatePhase,
    StateSnapshot,
    TaskSpec,
    TaskType,
)
from autonomous_software_factory.engines.circuit_breaker import CircuitBreaker


class InvalidStateTransitionError(Exception):
    def __init__(self, from_phase: StatePhase, to_phase: StatePhase, message: str = ""):
        msg = message or f"Illegal transition from '{from_phase.value}' to '{to_phase.value}'."
        super().__init__(msg)
        self.from_phase = from_phase
        self.to_phase = to_phase


class StateGraphEngine:
    """
    Industrial Typed StateGraph Engine implementing closed-loop control:
    Enforces deterministic state transitions, Human-in-the-Loop gates,
    reflexion loops, and Fast-Path autonomous routing (EARS-S1).
    """

    ALLOWED_TRANSITIONS: dict[StatePhase, set[StatePhase]] = {
        StatePhase.TRIAGE_SPEC: {
            StatePhase.HUMAN_GATE,
            StatePhase.CODER_TDD,  # Fast-Path bypass
            StatePhase.ABORTED,
        },
        StatePhase.HUMAN_GATE: {
            StatePhase.PLANNER,
            StatePhase.ABORTED,
        },
        StatePhase.PLANNER: {
            StatePhase.CODER_TDD,
            StatePhase.ABORTED,
        },
        StatePhase.CODER_TDD: {
            StatePhase.CODE_REVIEWER,
            StatePhase.CODER_TDD,  # Reflexion loop
            StatePhase.ABORTED,
        },
        StatePhase.CODE_REVIEWER: {
            StatePhase.ARTIFACT_PUBLISHER,
            StatePhase.CODER_TDD,  # Review rejection
            StatePhase.ABORTED,
        },
        StatePhase.ARTIFACT_PUBLISHER: {
            StatePhase.COMPLETED,
            StatePhase.ABORTED,
        },
        StatePhase.COMPLETED: set(),
        StatePhase.ABORTED: set(),
    }

    def __init__(self, task: TaskSpec):
        self.task = task
        self.current_phase: StatePhase = StatePhase.TRIAGE_SPEC
        self.step_index: int = 0
        self.context: dict[str, Any] = {}
        self.history: list[StateSnapshot] = []
        self._record_snapshot(reason="Initial initialization")

    def _record_snapshot(self, reason: str = "", circuit_status: CircuitStatus = CircuitStatus.OK) -> StateSnapshot:
        snapshot = StateSnapshot(
            snapshot_id=f"snap-{uuid.uuid4().hex[:8]}",
            task_id=self.task.task_id,
            phase=self.current_phase,
            step_index=self.step_index,
            context=dict(self.context),
            circuit_status=circuit_status,
        )
        self.history.append(snapshot)
        return snapshot

    def transition_to(
        self,
        target_phase: StatePhase,
        context_update: dict[str, Any] | None = None,
        reason: str = "",
        circuit_status: CircuitStatus = CircuitStatus.OK,
    ) -> StateSnapshot:
        """Transitions state machine to target phase if legal according to graph invariants."""
        allowed = self.ALLOWED_TRANSITIONS.get(self.current_phase, set())
        if target_phase not in allowed:
            raise InvalidStateTransitionError(
                from_phase=self.current_phase,
                to_phase=target_phase,
                message=f"Cannot transition from {self.current_phase} to {target_phase}.",
            )

        self.current_phase = target_phase
        self.step_index += 1
        if context_update:
            self.context.update(context_update)
        if reason:
            self.context["last_transition_reason"] = reason

        return self._record_snapshot(reason=reason, circuit_status=circuit_status)

    def route_initial_phase(self) -> None:
        """EARS-S1: If task is fast-path, bypasses gate and planner straight to Coder TDD."""
        if self.task.task_type == TaskType.FAST_PATH:
            self.transition_to(
                StatePhase.CODER_TDD,
                reason="Fast-Path route: bypassing gates for cosmetic/bugfix task",
            )

    def approve_human_gate(self) -> StateSnapshot:
        """Advances from HUMAN_GATE to PLANNER upon human approval."""
        return self.transition_to(
            StatePhase.PLANNER,
            context_update={"human_approved": True},
            reason="Human approval granted at Gate 1",
        )

    def reject_human_gate(self, reason: str = "Rejected by operator") -> StateSnapshot:
        """Aborts from HUMAN_GATE upon human rejection."""
        return self.transition_to(
            StatePhase.ABORTED,
            context_update={"human_approved": False, "reason": reason},
            reason=reason,
        )

    def evaluate_coder_oracle(
        self,
        oracle_result: OracleResult,
        circuit_breaker: CircuitBreaker,
    ) -> StateSnapshot:
        """
        Evaluates the deterministic oracle results in the CODER_TDD state.
        Passes to CODE_REVIEWER if tests pass (exit_code == 0).
        Loops in CODER_TDD if tests fail and circuit breaker is healthy.
        Aborts to ABORTED if circuit breaker is tripped.
        """
        if circuit_breaker.status != CircuitStatus.OK:
            return self.transition_to(
                StatePhase.ABORTED,
                context_update={"circuit_breaker_status": circuit_breaker.status.value},
                reason=f"Circuit breaker tripped: {circuit_breaker.status.value}",
                circuit_status=circuit_breaker.status,
            )

        if oracle_result.is_success:
            return self.transition_to(
                StatePhase.CODE_REVIEWER,
                context_update={"oracle_passed": True, "passed_tests": oracle_result.passed_tests},
                reason="Deterministic oracle passed with exit_code == 0",
            )
        else:
            # Reflexion loop: stay in CODER_TDD
            retries = self.context.get("retry_count", 0) + 1
            return self.transition_to(
                StatePhase.CODER_TDD,
                context_update={
                    "retry_count": retries,
                    "last_oracle_failure": oracle_result.stderr or oracle_result.stdout,
                },
                reason=f"Reflexion loop iteration {retries}: oracle exit_code != 0",
            )

    def is_terminal(self) -> bool:
        return self.current_phase in (StatePhase.COMPLETED, StatePhase.ABORTED)
