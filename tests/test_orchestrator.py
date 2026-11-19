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


def test_antigravity_worker_live_sdk_step_streams_thoughts_and_tool_calls_through_circuit_breaker(monkeypatch):
    from autonomous_software_factory.engines.circuit_breaker import CircuitBreaker

    class FakeToolCall:
        def __init__(self, name, args):
            self.name = name
            self.args = args

    class FakeResponse:
        def __init__(self, thoughts_list, calls_list):
            self._thoughts = thoughts_list
            self._calls = calls_list

        @property
        def thoughts(self):
            async def _gen():
                for t in self._thoughts:
                    yield t
            return _gen()

        @property
        def tool_calls(self):
            async def _gen():
                for c in self._calls:
                    yield c
            return _gen()

        def __aiter__(self):
            async def _gen():
                yield "Patch applied"
            return _gen()

    class FakeAgent:
        def __init__(self, config):
            self.config = config

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def chat(self, prompt: str):
            return FakeResponse(
                thoughts_list=["Analyzing stacktrace", "Writing minimal green patch"],
                calls_list=[FakeToolCall("edit_file", {"file": "calc.py", "line": 10})],
            )

    import google.antigravity as agy
    monkeypatch.setattr(agy, "Agent", FakeAgent)

    cb = CircuitBreaker(max_steps=8, max_cost_usd=0.25)
    worker = AntigravityWorkerAdapter(role="Coder")
    result = worker.execute_live_sdk_step(
        prompt="Fix margin formula",
        circuit_breaker=cb,
        api_key="AIzaFakeKey123",
    )

    assert result["status"] == "live_sdk_step_executed"
    assert len(cb.thoughts) == 2
    assert cb.tracker.current_steps == 1
    assert result["tool_calls_count"] == 1


def test_antigravity_worker_live_sdk_step_trips_oscillation_on_duplicate_sdk_tool_call(monkeypatch):
    from autonomous_software_factory.engines.circuit_breaker import (
        CircuitBreaker,
        CircuitBreakerTrippedError,
    )

    class FakeToolCall:
        def __init__(self, name, args):
            self.name = name
            self.args = args

    class FakeResponse:
        @property
        def thoughts(self):
            async def _gen():
                yield "Repeating same broken patch"
            return _gen()

        @property
        def tool_calls(self):
            async def _gen():
                yield FakeToolCall("edit_file", {"file": "calc.py", "patch": "same"})
                yield FakeToolCall("edit_file", {"file": "calc.py", "patch": "same"})
            return _gen()

        def __aiter__(self):
            async def _gen():
                yield ""
            return _gen()

    class FakeAgent:
        def __init__(self, config):
            self.config = config

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def chat(self, prompt: str):
            return FakeResponse()

    import google.antigravity as agy
    monkeypatch.setattr(agy, "Agent", FakeAgent)

    cb = CircuitBreaker(max_steps=8, max_cost_usd=0.25)
    worker = AntigravityWorkerAdapter(role="Coder")

    with pytest.raises(CircuitBreakerTrippedError) as exc_info:
        worker.execute_live_sdk_step(
            prompt="Looping prompt",
            circuit_breaker=cb,
            api_key="AIzaFakeKey123",
        )

    assert exc_info.value.status == CircuitStatus.TRIPPED_OSCILLATION

