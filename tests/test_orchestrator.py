import pytest
from autonomous_software_factory.domain.models import (
    CircuitStatus,
    OracleResult,
    StatePhase,
    TaskSpec,
    TaskType,
)
from autonomous_software_factory.engines.circuit_breaker import CircuitBreaker
from autonomous_software_factory.engines.oracle import DeterministicOracle
from autonomous_software_factory.engines.reflexion import ReflexionEngine
from autonomous_software_factory.engines.state_engine import StateGraphEngine
from autonomous_software_factory.services.checkpoint_service import SQLiteCheckpointService
from autonomous_software_factory.connectors.agent_worker import AntigravityWorkerAdapter
from autonomous_software_factory.services.orchestrator import FactoryOrchestrator


class MockOracle(DeterministicOracle):
    def __init__(self, sequence: list[OracleResult]):
        super().__init__()
        self.sequence = list(sequence)
        self.call_count = 0

    def execute_suite(self, cmd=None, cwd=None, timeout=None):
        if self.call_count < len(self.sequence):
            res = self.sequence[self.call_count]
        else:
            res = self.sequence[-1]
        self.call_count += 1
        return res


def test_orchestrator_multi_agent_success(tmp_path):
    db_path = str(tmp_path / "orch_success.db")
    checkpointer = SQLiteCheckpointService(db_path=db_path)
    oracle = MockOracle([OracleResult(exit_code=0, passed_tests=3)])

    orchestrator = FactoryOrchestrator(
        checkpoint_service=checkpointer,
        oracle=oracle,
    )

    task = TaskSpec(
        task_id="task-multi-01",
        title="Add Cashflow Aggregator",
        description="Aggregate cashflow across business units",
        task_type=TaskType.MULTI_AGENT,
    )

    report = orchestrator.execute_task(task, auto_approve_gate=True)

    assert report["is_success"] is True
    assert report["final_phase"] == StatePhase.COMPLETED
    assert report["circuit_status"] == CircuitStatus.OK
    assert report["total_steps"] > 0
    assert report["snapshots_recorded"] >= 5

    # Check persistence in SQLite
    persisted = checkpointer.list_snapshots("task-multi-01")
    assert len(persisted) >= 5
    assert persisted[-1].phase == StatePhase.COMPLETED


def test_orchestrator_reflexion_retry_then_success(tmp_path):
    db_path = str(tmp_path / "orch_retry.db")
    checkpointer = SQLiteCheckpointService(db_path=db_path)
    # Fail once, pass second time
    oracle = MockOracle([
        OracleResult(exit_code=1, failed_tests=1, stderr="AssertionError: 10 != 12"),
        OracleResult(exit_code=0, passed_tests=2),
    ])

    orchestrator = FactoryOrchestrator(
        checkpoint_service=checkpointer,
        oracle=oracle,
    )

    task = TaskSpec(
        task_id="task-retry-02",
        title="Fix margin calculator",
        description="Update gross margin formula",
        task_type=TaskType.MULTI_AGENT,
    )

    report = orchestrator.execute_task(task, auto_approve_gate=True)

    assert report["is_success"] is True
    assert report["final_phase"] == StatePhase.COMPLETED
    assert oracle.call_count == 2
    assert report["retries"] == 1


def test_orchestrator_fast_path_execution(tmp_path):
    db_path = str(tmp_path / "orch_fast.db")
    checkpointer = SQLiteCheckpointService(db_path=db_path)
    oracle = MockOracle([OracleResult(exit_code=0, passed_tests=1)])

    orchestrator = FactoryOrchestrator(
        checkpoint_service=checkpointer,
        oracle=oracle,
    )

    task = TaskSpec(
        task_id="task-fast-03",
        title="Fix typo in config",
        description="Cosmetic typo",
        task_type=TaskType.FAST_PATH,
    )

    report = orchestrator.execute_task(task)

    assert report["is_success"] is True
    assert report["final_phase"] == StatePhase.COMPLETED

    # Verify that Planner and Human Gate were bypassed (EARS-S1)
    phases = [s.phase for s in checkpointer.list_snapshots("task-fast-03")]
    assert StatePhase.HUMAN_GATE not in phases
    assert StatePhase.PLANNER not in phases


def test_orchestrator_halts_on_oscillation(tmp_path):
    db_path = str(tmp_path / "orch_oscillation.db")
    checkpointer = SQLiteCheckpointService(db_path=db_path)
    oracle = MockOracle([OracleResult(exit_code=1, failed_tests=1)])

    worker = AntigravityWorkerAdapter(simulate_oscillation=True)
    orchestrator = FactoryOrchestrator(
        checkpoint_service=checkpointer,
        oracle=oracle,
        worker=worker,
    )

    task = TaskSpec(
        task_id="task-osc-04",
        title="Infinite loop task",
        description="Repeats identical tool call",
        task_type=TaskType.MULTI_AGENT,
    )

    report = orchestrator.execute_task(task, auto_approve_gate=True)

    assert report["is_success"] is False
    assert report["final_phase"] == StatePhase.ABORTED
    assert report["circuit_status"] == CircuitStatus.TRIPPED_OSCILLATION
