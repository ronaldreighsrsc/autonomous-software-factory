import pytest
from autonomous_software_factory.domain.models import (
    BudgetConfig,
    BudgetTracker,
    CircuitStatus,
    OracleResult,
    StatePhase,
    StateSnapshot,
    TaskSpec,
    TaskType,
    ToolCall,
)


def test_tool_call_action_hash_deterministic():
    tc1 = ToolCall(name="edit_file", args={"path": "a.py", "content": "print(1)"})
    tc2 = ToolCall(name="edit_file", args={"content": "print(1)", "path": "a.py"})
    # Order of dict keys shouldn't affect hash
    assert tc1.action_hash == tc2.action_hash
    assert len(tc1.action_hash) == 64


def test_oracle_result_success_deterministic():
    success_result = OracleResult(exit_code=0, passed_tests=5, failed_tests=0)
    assert success_result.is_success is True

    failed_result = OracleResult(exit_code=1, passed_tests=4, failed_tests=1)
    assert failed_result.is_success is False


def test_budget_tracker_limits():
    cfg = BudgetConfig(max_steps=3, max_cost_usd=0.05, cost_per_step_usd=0.02)
    tracker = BudgetTracker(config=cfg)

    assert not tracker.is_steps_exceeded()
    assert not tracker.is_cost_exceeded()

    tracker.record_step()  # step 1, cost 0.02
    tracker.record_step()  # step 2, cost 0.04
    assert not tracker.is_cost_exceeded()

    tracker.record_step()  # step 3, cost 0.06 -> cost exceeded
    assert tracker.is_cost_exceeded()
    assert not tracker.is_steps_exceeded()

    tracker.record_step()  # step 4, cost 0.08 -> steps exceeded
    assert tracker.is_steps_exceeded()


def test_state_snapshot_serialization():
    snap = StateSnapshot(
        snapshot_id="snap-001",
        task_id="task-123",
        phase=StatePhase.CODER_TDD,
        step_index=2,
        context={"test_passed": False},
        circuit_status=CircuitStatus.OK,
    )
    data = snap.model_dump()
    assert data["snapshot_id"] == "snap-001"
    assert data["phase"] == "coder_tdd"
    restored = StateSnapshot.model_validate(data)
    assert restored.phase == StatePhase.CODER_TDD
