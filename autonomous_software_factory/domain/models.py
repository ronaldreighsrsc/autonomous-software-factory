from enum import Enum
import hashlib
import json
import time
from typing import Any
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    FAST_PATH = "fast_path"
    MULTI_AGENT = "multi_agent"


class StatePhase(str, Enum):
    TRIAGE_SPEC = "triage_spec"
    HUMAN_GATE = "human_gate"
    PLANNER = "planner"
    CODER_TDD = "coder_tdd"
    CODE_REVIEWER = "code_reviewer"
    ARTIFACT_PUBLISHER = "artifact_publisher"
    COMPLETED = "completed"
    ABORTED = "aborted"


class CircuitStatus(str, Enum):
    OK = "ok"
    TRIPPED_OSCILLATION = "tripped_oscillation"
    TRIPPED_COST = "tripped_cost"
    TRIPPED_STEPS = "tripped_steps"
    ESCALATED = "escalated"


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

    @property
    def action_hash(self) -> str:
        """Deterministic SHA-256 fingerprint of the tool name and arguments."""
        canonical_payload = json.dumps(
            {"name": self.name, "args": self.args},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


class OracleResult(BaseModel):
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    passed_tests: int = 0
    failed_tests: int = 0
    coverage_percent: float = 0.0
    command: str = "pytest"

    @property
    def is_success(self) -> bool:
        """Deterministic oracle: only zero exit code represents success."""
        return self.exit_code == 0


class BudgetConfig(BaseModel):
    max_steps: int = 8
    max_cost_usd: float = 0.25
    cost_per_step_usd: float = 0.015


class BudgetTracker(BaseModel):
    current_steps: int = 0
    current_cost_usd: float = 0.0
    config: BudgetConfig = Field(default_factory=BudgetConfig)

    def record_step(self, additional_cost: float | None = None) -> None:
        self.current_steps += 1
        self.current_cost_usd += (
            additional_cost if additional_cost is not None else self.config.cost_per_step_usd
        )

    def is_steps_exceeded(self) -> bool:
        return self.current_steps > self.config.max_steps

    def is_cost_exceeded(self) -> bool:
        return self.current_cost_usd > self.config.max_cost_usd


class StateSnapshot(BaseModel):
    snapshot_id: str
    task_id: str
    phase: StatePhase
    step_index: int = 0
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    circuit_status: CircuitStatus = CircuitStatus.OK


class TaskSpec(BaseModel):
    task_id: str
    title: str
    description: str
    task_type: TaskType = TaskType.MULTI_AGENT
    target_files: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
