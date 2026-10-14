import pytest
from typer.testing import CliRunner
from autonomous_software_factory.cli import app
from autonomous_software_factory.domain.models import CircuitStatus, StatePhase, StateSnapshot
from autonomous_software_factory.services.checkpoint_service import SQLiteCheckpointService

runner = CliRunner()


from unittest.mock import patch
from autonomous_software_factory.domain.models import OracleResult


def test_cli_run_command_fast_path(tmp_path):
    db_file = str(tmp_path / "cli_test.db")
    with patch(
        "autonomous_software_factory.engines.oracle.DeterministicOracle.execute_suite",
        return_value=OracleResult(exit_code=0, passed_tests=1),
    ):
        result = runner.invoke(
            app,
            [
                "run",
                "Fix cosmetic typo in docstring",
                "--db", db_file,
                "--fast-path",
                "--task-id", "cli-task-01",
            ],
        )
    assert result.exit_code == 0
    assert "EJECUCIÓN FINALIZADA" in result.output
    assert "cli-task-01" in result.output


def test_cli_inspect_command(tmp_path):
    db_file = str(tmp_path / "inspect_test.db")
    service = SQLiteCheckpointService(db_path=db_file)
    service.save_snapshot(
        StateSnapshot(
            snapshot_id="snap-cli-99",
            task_id="task-inspect-01",
            phase=StatePhase.CODER_TDD,
            step_index=2,
            context={"note": "inspect me"},
            circuit_status=CircuitStatus.OK,
        )
    )

    result = runner.invoke(
        app,
        ["inspect", "task-inspect-01", "--db", db_file],
    )
    assert result.exit_code == 0
    assert "snap-cli-99" in result.output
    assert "coder_tdd" in result.output


def test_cli_rollback_command(tmp_path):
    db_file = str(tmp_path / "rollback_test.db")
    service = SQLiteCheckpointService(db_path=db_file)
    service.save_snapshot(
        StateSnapshot(
            snapshot_id="snap-target",
            task_id="task-rb",
            phase=StatePhase.PLANNER,
            step_index=1,
            context={},
        )
    )

    result = runner.invoke(
        app,
        ["rollback", "snap-target", "--db", db_file],
    )
    assert result.exit_code == 0
    assert "Rollback exitoso" in result.output
    assert "snap-target" in result.output


def test_cli_telemetry_command(tmp_path):
    db_file = str(tmp_path / "telemetry_test.db")
    service = SQLiteCheckpointService(db_path=db_file)
    service.save_snapshot(
        StateSnapshot(
            snapshot_id="snap-t1",
            task_id="task-a",
            phase=StatePhase.COMPLETED,
            step_index=4,
            context={},
        )
    )

    result = runner.invoke(
        app,
        ["telemetry", "--db", db_file],
    )
    assert result.exit_code == 0
    assert "AgentOps & Telemetría" in result.output
