import json
import sqlite3
from typing import Any
from autonomous_software_factory.domain.models import CircuitStatus, StatePhase, StateSnapshot


class SnapshotNotFoundError(Exception):
    def __init__(self, snapshot_id: str):
        super().__init__(f"Snapshot '{snapshot_id}' not found in checkpoint store.")
        self.snapshot_id = snapshot_id


class SQLiteCheckpointService:
    """
    Transactional SQLite Checkpointing Service with WAL Mode (Write-Ahead Logging).
    Enforces ACID persistence for StateGraph snapshots and provides Time-Travel Debugging (rollback).
    """

    def __init__(self, db_path: str = "factory_checkpoints.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enforce WAL mode and fast synchronous writes
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    context_json TEXT NOT NULL,
                    circuit_status TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_task_steps
                ON snapshots (task_id, step_index ASC);
                """
            )
            conn.commit()

    def save_snapshot(self, snapshot: StateSnapshot) -> None:
        """Persists a StateSnapshot into SQLite WAL."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO snapshots (
                    snapshot_id, task_id, phase, step_index,
                    context_json, circuit_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.task_id,
                    snapshot.phase.value,
                    snapshot.step_index,
                    json.dumps(snapshot.context, default=str),
                    snapshot.circuit_status.value,
                    snapshot.timestamp,
                ),
            )
            conn.commit()

    def get_snapshot(self, snapshot_id: str) -> StateSnapshot | None:
        """Retrieves a single snapshot by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snapshots WHERE snapshot_id = ?;",
                (snapshot_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_snapshot(row)

    def list_snapshots(self, task_id: str) -> list[StateSnapshot]:
        """Returns all snapshots for a given task in chronological order."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snapshots WHERE task_id = ? ORDER BY step_index ASC, created_at ASC;",
                (task_id,),
            )
            rows = cursor.fetchall()
            return [self._row_to_snapshot(r) for r in rows]

    def rollback_to(self, snapshot_id: str) -> StateSnapshot:
        """
        Time-Travel: Reverts system state to a historical checkpoint.
        Prunes any subsequent orphaned steps if necessary.
        """
        target = self.get_snapshot(snapshot_id)
        if not target:
            raise SnapshotNotFoundError(snapshot_id)

        # Rollback: prune subsequent divergent steps
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM snapshots WHERE task_id = ? AND step_index > ?;",
                (target.task_id, target.step_index),
            )
            conn.commit()

        return target

    def _row_to_snapshot(self, row: sqlite3.Row) -> StateSnapshot:
        return StateSnapshot(
            snapshot_id=row["snapshot_id"],
            task_id=row["task_id"],
            phase=StatePhase(row["phase"]),
            step_index=row["step_index"],
            context=json.loads(row["context_json"]),
            circuit_status=CircuitStatus(row["circuit_status"]),
            timestamp=row["created_at"],
        )
