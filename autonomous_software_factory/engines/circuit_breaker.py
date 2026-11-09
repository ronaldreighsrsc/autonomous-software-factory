import hashlib
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
    Industrial closed-loop circuit breaker implementing EARS-U2 & Vertical Slice /pair invariants:
    1. Anti-oscillation: Trips if identical tool call with identical arguments repeats consecutively.
    2. Step budgeting: Trips if auto-correction exceeds max_steps (default 8).
    3. Cost budgeting: Trips if total cost exceeds max_cost_usd (default $0.25).
    4. Test Tampering Guard: Cryptographically locks red-phase tests via SHA-256 and blocks edits/deletions during green/fixer phase.
    5. Blast-Radius Guard (Vertical Slice): Trips if a step modifies more than max_files_per_step (default 3) or max_diff_lines (default 100).
    """

    MUTATING_FILE_TOOLS = frozenset({"edit_file", "write_file", "delete_file", "patch_file", "multi_edit"})

    def __init__(
        self,
        max_steps: int = 8,
        max_cost_usd: float = 0.25,
        cost_per_step_usd: float = 0.015,
        max_files_per_step: int = 3,
        max_diff_lines: int = 100,
    ):
        self.tracker = BudgetTracker(
            config=BudgetConfig(
                max_steps=max_steps,
                max_cost_usd=max_cost_usd,
                cost_per_step_usd=cost_per_step_usd,
            )
        )
        self.max_files_per_step = max_files_per_step
        self.max_diff_lines = max_diff_lines
        self.status: CircuitStatus = CircuitStatus.OK
        self.call_history: list[ToolCall] = []
        self.thoughts: list[str] = []
        self._locked_test_hashes: dict[str, str] = {}

    def record_thought(self, thought: str) -> None:
        self.thoughts.append(thought)

    def lock_test_suite(self, test_files: dict[str, str]) -> None:
        """Records SHA-256 hashes of red-phase tests so the green/fixer agent cannot tamper with them."""
        self._locked_test_hashes = {
            path.replace("\\", "/"): hashlib.sha256(content.encode("utf-8")).hexdigest()
            for path, content in test_files.items()
        }

    def verify_test_integrity(self, current_test_files: dict[str, str]) -> bool:
        """Verifies that locked red-phase test files have not been modified or deleted."""
        if not self._locked_test_hashes:
            return True
        normalized_current = {
            path.replace("\\", "/"): hashlib.sha256(content.encode("utf-8")).hexdigest()
            for path, content in current_test_files.items()
        }
        for locked_path, expected_hash in self._locked_test_hashes.items():
            actual_hash = normalized_current.get(locked_path)
            if actual_hash != expected_hash:
                self.status = CircuitStatus.TRIPPED_TEST_TAMPERING
                reason = (
                    f"Test tampering detected: locked test file '{locked_path}' "
                    f"was altered or deleted during green/fixer phase."
                )
                raise CircuitBreakerTrippedError(status=self.status, reason=reason)
        return True

    def verify_blast_radius(self, modified_files: list[str], diff_lines: int = 0) -> bool:
        """Enforces Vertical Slice scope limits (max files and max diff lines per step)."""
        unique_files = {p.replace("\\", "/") for p in modified_files}
        if len(unique_files) > self.max_files_per_step:
            self.status = CircuitStatus.TRIPPED_BLAST_RADIUS
            reason = (
                f"Blast-radius exceeded: step modified {len(unique_files)} files "
                f"(max allowed per Vertical Slice step is {self.max_files_per_step})."
            )
            raise CircuitBreakerTrippedError(status=self.status, reason=reason)
        if diff_lines > self.max_diff_lines:
            self.status = CircuitStatus.TRIPPED_BLAST_RADIUS
            reason = (
                f"Blast-radius exceeded: step changed {diff_lines} lines "
                f"(max allowed per Vertical Slice step is {self.max_diff_lines})."
            )
            raise CircuitBreakerTrippedError(status=self.status, reason=reason)
        return True

    def verify_safety(self, tool_name: str, args: dict[str, Any] | None = None) -> bool:
        """
        Validates safety before executing a tool call.
        Trips on test-tampering attempts or consecutive identical calls (anti-oscillation).
        """
        safe_args = args or {}
        if self._locked_test_hashes and tool_name in self.MUTATING_FILE_TOOLS:
            target_path = str(safe_args.get("path") or safe_args.get("Path") or "").replace("\\", "/")
            if target_path in self._locked_test_hashes or target_path.startswith("tests/"):
                self.status = CircuitStatus.TRIPPED_TEST_TAMPERING
                reason = (
                    f"Test tampering blocked: agent attempted '{tool_name}' on locked test '{target_path}' "
                    f"during green/fixer phase."
                )
                raise CircuitBreakerTrippedError(status=self.status, reason=reason)

        call = ToolCall(name=tool_name, args=safe_args)

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
