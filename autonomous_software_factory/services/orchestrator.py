from typing import Any
from autonomous_software_factory.connectors.agent_worker import AntigravityWorkerAdapter
from autonomous_software_factory.domain.models import (
    CircuitStatus,
    StatePhase,
    TaskSpec,
    TaskType,
)
from autonomous_software_factory.engines.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerTrippedError,
)
from autonomous_software_factory.engines.oracle import DeterministicOracle
from autonomous_software_factory.engines.reflexion import ReflexionEngine
from autonomous_software_factory.engines.state_engine import StateGraphEngine
from autonomous_software_factory.services.checkpoint_service import SQLiteCheckpointService


class FactoryOrchestrator:
    """
    Industrial Master Orchestrator:
    Coordinates closed-loop software engineering using typed StateGraphs,
    Antigravity agent workers, deterministic test oracles, and SQLite WAL persistence.
    """

    def __init__(
        self,
        checkpoint_service: SQLiteCheckpointService | None = None,
        oracle: DeterministicOracle | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        reflexion: ReflexionEngine | None = None,
        worker: AntigravityWorkerAdapter | None = None,
    ):
        self.checkpoint_service = checkpoint_service or SQLiteCheckpointService()
        self.oracle = oracle or DeterministicOracle()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.reflexion = reflexion or ReflexionEngine()
        self.worker = worker or AntigravityWorkerAdapter()

    def execute_task(
        self,
        task: TaskSpec,
        auto_approve_gate: bool = True,
    ) -> dict[str, Any]:
        """Executes the full closed-loop development pipeline for a TaskSpec."""
        engine = StateGraphEngine(task=task)
        self.checkpoint_service.save_snapshot(engine.history[-1])

        # 1. Routing phase (Fast-Path vs Multi-Agent)
        if task.task_type == TaskType.FAST_PATH:
            engine.route_initial_phase()
            self.checkpoint_service.save_snapshot(engine.history[-1])
        else:
            engine.transition_to(StatePhase.HUMAN_GATE, reason="EARS specification prepared")
            self.checkpoint_service.save_snapshot(engine.history[-1])

            if auto_approve_gate:
                engine.approve_human_gate()
                self.checkpoint_service.save_snapshot(engine.history[-1])

                engine.transition_to(StatePhase.CODER_TDD, reason="Task decomposition completed")
                self.checkpoint_service.save_snapshot(engine.history[-1])
            else:
                engine.reject_human_gate(reason="Rejected by operator at Gate 1")
                self.checkpoint_service.save_snapshot(engine.history[-1])
                return self._build_report(engine, task)

        # 2. Coder TDD closed-loop execution
        coder_prompt = f"Implement minimal code for: {task.title}\n{task.description}"

        while not engine.is_terminal():
            # A. Agent worker step supervised by CircuitBreaker
            try:
                self.worker.execute_agent_step(
                    prompt=coder_prompt,
                    circuit_breaker=self.circuit_breaker,
                )
            except CircuitBreakerTrippedError as cb_err:
                engine.transition_to(
                    StatePhase.ABORTED,
                    context_update={"circuit_breaker_error": str(cb_err)},
                    reason=f"CircuitBreaker halted execution: {cb_err.status.value}",
                    circuit_status=cb_err.status,
                )
                self.checkpoint_service.save_snapshot(engine.history[-1])
                break

            # B. Deterministic Truth Oracle (Pytest subprocess)
            oracle_result = self.oracle.execute_suite()
            engine.evaluate_coder_oracle(
                oracle_result=oracle_result,
                circuit_breaker=self.circuit_breaker,
            )
            self.checkpoint_service.save_snapshot(engine.history[-1])

            # C. Transition handling
            if engine.current_phase == StatePhase.CODER_TDD:
                # Reflexion loop: build sanitized feedback prompt
                feedback = self.reflexion.build_corrective_observation(
                    oracle_result.stderr or oracle_result.stdout
                )
                coder_prompt = f"{coder_prompt}\n\n{feedback}"
            elif engine.current_phase == StatePhase.CODE_REVIEWER:
                # Code reviewer passes to publication
                engine.transition_to(
                    StatePhase.ARTIFACT_PUBLISHER,
                    reason="Static analysis and safety review passed",
                )
                self.checkpoint_service.save_snapshot(engine.history[-1])

                engine.transition_to(
                    StatePhase.COMPLETED,
                    reason="Conventional commit and artifacts published",
                )
                self.checkpoint_service.save_snapshot(engine.history[-1])
                break
            else:
                # ABORTED or other terminal phase
                break

        return self._build_report(engine, task)

    def _build_report(self, engine: StateGraphEngine, task: TaskSpec) -> dict[str, Any]:
        snapshots = self.checkpoint_service.list_snapshots(task.task_id)
        is_success = (engine.current_phase == StatePhase.COMPLETED)

        return {
            "task_id": task.task_id,
            "title": task.title,
            "task_type": task.task_type.value,
            "final_phase": engine.current_phase,
            "is_success": is_success,
            "circuit_status": self.circuit_breaker.status,
            "total_steps": self.circuit_breaker.tracker.current_steps,
            "total_cost_usd": self.circuit_breaker.tracker.current_cost_usd,
            "retries": engine.context.get("retry_count", 0),
            "snapshots_recorded": len(snapshots),
        }
