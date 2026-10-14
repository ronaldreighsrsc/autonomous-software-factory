import pytest
from autonomous_software_factory.domain.models import (
    CircuitStatus,
    OracleResult,
    StatePhase,
    TaskSpec,
    TaskType,
)
from autonomous_software_factory.engines.circuit_breaker import CircuitBreaker
from autonomous_software_factory.engines.state_engine import (
    InvalidStateTransitionError,
    StateGraphEngine,
)


def test_state_engine_full_multi_agent_lifecycle():
    task = TaskSpec(
        task_id="task-001",
        title="Add Data Netting Engine",
        description="Complex financial netting logic",
        task_type=TaskType.MULTI_AGENT,
    )
    engine = StateGraphEngine(task=task)
    assert engine.current_phase == StatePhase.TRIAGE_SPEC

    # 1. Spec triage completed -> Move to Human Gate
    engine.transition_to(StatePhase.HUMAN_GATE, reason="EARS spec generated")
    assert engine.current_phase == StatePhase.HUMAN_GATE

    # 2. Human approves Gate 1 -> Planner
    engine.approve_human_gate()
    assert engine.current_phase == StatePhase.PLANNER

    # 3. Plan generated -> Coder TDD
    engine.transition_to(StatePhase.CODER_TDD, reason="Atomic tasks decomposed")
    assert engine.current_phase == StatePhase.CODER_TDD

    # 4. Oracle passes -> Reviewer
    oracle_pass = OracleResult(exit_code=0, passed_tests=5)
    cb = CircuitBreaker()
    engine.evaluate_coder_oracle(oracle_result=oracle_pass, circuit_breaker=cb)
    assert engine.current_phase == StatePhase.CODE_REVIEWER

    # 5. Reviewer passes -> Publisher
    engine.transition_to(StatePhase.ARTIFACT_PUBLISHER, reason="Linters and security passed")
    assert engine.current_phase == StatePhase.ARTIFACT_PUBLISHER

    # 6. Publish -> Completed
    engine.transition_to(StatePhase.COMPLETED, reason="Git commit pushed")
    assert engine.current_phase == StatePhase.COMPLETED
    assert engine.is_terminal() is True


def test_state_engine_human_gate_rejection():
    task = TaskSpec(
        task_id="task-002",
        title="Risky refactor",
        description="Untested overhaul",
        task_type=TaskType.MULTI_AGENT,
    )
    engine = StateGraphEngine(task=task)
    engine.transition_to(StatePhase.HUMAN_GATE)
    engine.reject_human_gate(reason="Scope too wide, refactor rejected")

    assert engine.current_phase == StatePhase.ABORTED
    assert engine.is_terminal() is True
    assert "rejected" in engine.history[-1].context.get("reason", "")


def test_state_engine_fast_path_routing():
    task = TaskSpec(
        task_id="task-003",
        title="Fix typo in README",
        description="Cosmetic typo",
        task_type=TaskType.FAST_PATH,
    )
    engine = StateGraphEngine(task=task)
    assert engine.current_phase == StatePhase.TRIAGE_SPEC

    # Fast-Path skips Human Gate & Planner directly to Coder TDD (EARS-S1)
    engine.route_initial_phase()
    assert engine.current_phase == StatePhase.CODER_TDD


def test_state_engine_reflexion_loop_on_oracle_failure():
    task = TaskSpec(
        task_id="task-004",
        title="Implement parser",
        description="Math parser",
        task_type=TaskType.MULTI_AGENT,
    )
    engine = StateGraphEngine(task=task)
    engine.current_phase = StatePhase.CODER_TDD

    cb = CircuitBreaker(max_steps=5)
    oracle_fail = OracleResult(exit_code=1, failed_tests=1)

    # First test failure: stays in CODER_TDD with reflexion loop
    engine.evaluate_coder_oracle(oracle_result=oracle_fail, circuit_breaker=cb)
    assert engine.current_phase == StatePhase.CODER_TDD
    assert engine.context.get("retry_count") == 1


def test_state_engine_aborts_when_circuit_breaker_tripped():
    task = TaskSpec(
        task_id="task-005",
        title="Bugfix loop",
        description="Oscillating bug",
        task_type=TaskType.MULTI_AGENT,
    )
    engine = StateGraphEngine(task=task)
    engine.current_phase = StatePhase.CODER_TDD

    cb = CircuitBreaker(max_steps=2)
    cb.status = CircuitStatus.TRIPPED_OSCILLATION
    oracle_fail = OracleResult(exit_code=1, failed_tests=1)

    engine.evaluate_coder_oracle(oracle_result=oracle_fail, circuit_breaker=cb)
    assert engine.current_phase == StatePhase.ABORTED
    assert engine.is_terminal() is True


def test_state_engine_invalid_transition_rejected():
    task = TaskSpec(task_id="task-006", title="Test", description="Desc")
    engine = StateGraphEngine(task=task)
    assert engine.current_phase == StatePhase.TRIAGE_SPEC

    # Cannot jump directly from TRIAGE_SPEC to COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        engine.transition_to(StatePhase.COMPLETED)
