from typing import Any
from autonomous_software_factory.domain.models import (
    BudgetConfig,
    BudgetTracker,
    CircuitStatus,
    ToolCall,
)


class CircuitBreakerTrippedError(Exception):
    def __init__(self, status: CircuitStatus, reason: str):
        super().__init__(reason)
        self.status = status
        self.reason = reason


class CircuitBreaker:
    """
    Industrial closed-loop circuit breaker implementing EARS-U2:
    1. Anti-oscillation: Trips if identical tool call with identical arguments repeats consecutively.
    2. Step budgeting: Trips if auto-correction exceeds max_steps (default 8).
    3. Cost budgeting: Trips if total cost exceeds max_cost_usd (default $0.25).
    """

    def __init__(
        self,
        max_steps: int = 8,
        max_cost_usd: float = 0.25,
        cost_per_step_usd: float = 0.015,
    ):
        self.tracker = BudgetTracker(
            config=BudgetConfig(
                max_steps=max_steps,
                max_cost_usd=max_cost_usd,
                cost_per_step_usd=cost_per_step_usd,
            )
        )
        self.status: CircuitStatus = CircuitStatus.OK
        self.call_history: list[ToolCall] = []
        self.thoughts: list[str] = []

    def record_thought(self, thought: str) -> None:
        self.thoughts.append(thought)

    def verify_safety(self, tool_name: str, args: dict[str, Any] | None = None) -> bool:
        """
        Validates safety before executing a tool call.
        Trips on consecutive identical calls (anti-oscillation).
        """
        call = ToolCall(name=tool_name, args=args or {})

        if self.call_history:
            last_call = self.call_history[-1]
            if last_call.action_hash == call.action_hash:
                self.status = CircuitStatus.TRIPPED_OSCILLATION
                reason = (
                    f"Anti-oscillation triggered: identical tool '{tool_name}' "
                    f"with identical arguments executed consecutively (hash: {call.action_hash[:12]})."
                )
                raise CircuitBreakerTrippedError(status=self.status, reason=reason)

        self.call_history.append(call)
        return True

    def record_step(self, additional_cost: float | None = None) -> None:
        """
        Advances the execution step counter and evaluates step and cost budgets.
        """
        self.tracker.record_step(additional_cost=additional_cost)

        if self.tracker.is_cost_exceeded():
            self.status = CircuitStatus.TRIPPED_COST
            reason = (
                f"Cost budget exceeded: ${self.tracker.current_cost_usd:.4f} USD "
                f"> max ${self.tracker.config.max_cost_usd:.2f} USD."
            )
            raise CircuitBreakerTrippedError(status=self.status, reason=reason)

        if self.tracker.is_steps_exceeded():
            self.status = CircuitStatus.TRIPPED_STEPS
            reason = (
                f"Step budget exceeded: {self.tracker.current_steps} "
                f"> max allowed {self.tracker.config.max_steps}."
            )
            raise CircuitBreakerTrippedError(status=self.status, reason=reason)
