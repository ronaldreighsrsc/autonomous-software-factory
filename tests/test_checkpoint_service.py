import pytest
from autonomous_software_factory.domain.models import CircuitStatus, StatePhase, StateSnapshot
from autonomous_software_factory.services.checkpoint_service import (
    SQLiteCheckpointService,
    SnapshotNotFoundError,
)


def test_sqlite_checkpoint_initialization_and_save(tmp_path):
    db_path = str(tmp_path / "factory_state.db")
    service = SQLiteCheckpointService(db_path=db_path)

    snapshot = StateSnapshot(
        snapshot_id="snap-100",
        task_id="task-42",
        phase=StatePhase.CODER_TDD,
        step_index=3,
        context={"retry_count": 1, "target": "calc.py"},
        circuit_status=CircuitStatus.OK,
    )

    service.save_snapshot(snapshot)
    loaded = service.get_snapshot("snap-100")

    assert loaded is not None
    assert loaded.snapshot_id == "snap-100"
    assert loaded.task_id == "task-42"
    assert loaded.phase == StatePhase.CODER_TDD
    assert loaded.step_index == 3
    assert loaded.context["target"] == "calc.py"


def test_sqlite_checkpoint_list_history(tmp_path):
    db_path = str(tmp_path / "history.db")
    service = SQLiteCheckpointService(db_path=db_path)

    for i, phase in enumerate([StatePhase.TRIAGE_SPEC, StatePhase.HUMAN_GATE, StatePhase.PLANNER]):
        service.save_snapshot(
            StateSnapshot(
                snapshot_id=f"snap-{i}",
                task_id="task-99",
                phase=phase,
                step_index=i,
                context={},
            )
        )

    history = service.list_snapshots("task-99")
    assert len(history) == 3
    assert [s.phase for s in history] == [
        StatePhase.TRIAGE_SPEC,
        StatePhase.HUMAN_GATE,
        StatePhase.PLANNER,
    ]


def test_sqlite_checkpoint_time_travel_rollback(tmp_path):
    db_path = str(tmp_path / "timetravel.db")
    service = SQLiteCheckpointService(db_path=db_path)

    snap1 = StateSnapshot(
        snapshot_id="snap-step1",
        task_id="task-tt",
        phase=StatePhase.PLANNER,
        step_index=1,
        context={"valid_plan": True},
    )
    snap2 = StateSnapshot(
        snapshot_id="snap-step2",
        task_id="task-tt",
        phase=StatePhase.CODER_TDD,
        step_index=2,
        context={"diverged_code": True},
    )
    service.save_snapshot(snap1)
    service.save_snapshot(snap2)

    # Time-travel rollback to step 1
    rolled_back = service.rollback_to("snap-step1")
    assert rolled_back.snapshot_id == "snap-step1"
    assert rolled_back.phase == StatePhase.PLANNER
    assert rolled_back.context.get("valid_plan") is True


def test_sqlite_checkpoint_nonexistent_snapshot(tmp_path):
    db_path = str(tmp_path / "errors.db")
    service = SQLiteCheckpointService(db_path=db_path)

    with pytest.raises(SnapshotNotFoundError):
        service.rollback_to("snap-ghost")
