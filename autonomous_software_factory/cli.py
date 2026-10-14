import time
import uuid
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from autonomous_software_factory.domain.models import (
    StatePhase,
    TaskSpec,
    TaskType,
)
from autonomous_software_factory.engines.circuit_breaker import CircuitBreaker
from autonomous_software_factory.services.checkpoint_service import SQLiteCheckpointService
from autonomous_software_factory.services.orchestrator import FactoryOrchestrator

app = typer.Typer(
    help="Autonomous Software Factory — Motor Autónomo de Ingeniería de Software en Lazo Cerrado",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Requerimiento funcional o descripción del bug"),
    fast_path: bool = typer.Option(False, "--fast-path", "-f", help="Modo Fast-Path TDD directo (omite planificador)"),
    task_id: str = typer.Option("", "--task-id", "-t", help="Identificador personalizado de la tarea"),
    db: str = typer.Option("factory_checkpoints.db", "--db", help="Ruta de la base de datos SQLite WAL"),
    max_cost: float = typer.Option(0.25, "--max-cost", help="Tope de costo en USD"),
    max_steps: int = typer.Option(8, "--max-steps", help="Tope de pasos de auto-corrección"),
) -> None:
    """Ejecuta una tarea de ingeniería en lazo cerrado supervisada por oráculos y circuit breakers."""
    tid = task_id or f"task-{uuid.uuid4().hex[:6]}"
    task_type = TaskType.FAST_PATH if fast_path else TaskType.MULTI_AGENT

    console.print(
        Panel.fit(
            f"[bold cyan]Autonomous Software Factory[/bold cyan]\n"
            f"[bold white]Tarea:[/bold white] {tid}\n"
            f"[bold white]Modo:[/bold white] {task_type.value.upper()}\n"
            f"[bold white]Requerimiento:[/bold white] {prompt}\n"
            f"[bold white]Límites:[/bold white] Max ${max_cost:.2f} USD | Max {max_steps} Pasos",
            border_style="cyan",
            title="[bold yellow]🚀 Iniciando Ciclo en Lazo Cerrado[/bold yellow]",
        )
    )

    task = TaskSpec(
        task_id=tid,
        title=prompt[:60],
        description=prompt,
        task_type=task_type,
    )

    cb = CircuitBreaker(max_steps=max_steps, max_cost_usd=max_cost)
    checkpointer = SQLiteCheckpointService(db_path=db)
    orchestrator = FactoryOrchestrator(
        checkpoint_service=checkpointer,
        circuit_breaker=cb,
    )

    report = orchestrator.execute_task(task, auto_approve_gate=True)

    status_color = "green" if report["is_success"] else "red"
    result_text = "ÉXITO" if report["is_success"] else "ABORTADO / FALLIDO"

    table = Table(title="[bold yellow]📊 Reporte de Telemetría AgentOps[/bold yellow]", border_style="cyan")
    table.add_column("Métrica", style="bold white")
    table.add_column("Valor", style=f"bold {status_color}")

    table.add_row("Estado Final", str(report["final_phase"]))
    table.add_row("Resultado", result_text)
    table.add_row("Disyuntor (Circuit Breaker)", str(report["circuit_status"]))
    table.add_row("Pasos Ejecutados", str(report["total_steps"]))
    table.add_row("Costo Acumulado", f"${report['total_cost_usd']:.4f} USD")
    table.add_row("Reintentos de Reflexión", str(report["retries"]))
    table.add_row("Snapshots Persistidos", str(report["snapshots_recorded"]))

    console.print(table)
    console.print(f"[bold {status_color}]>> EJECUCIÓN FINALIZADA PARA {tid}[/bold {status_color}]\n")


@app.command()
def inspect(
    task_id: str = typer.Argument(..., help="Identificador de la tarea a auditar"),
    db: str = typer.Option("factory_checkpoints.db", "--db", help="Ruta de SQLite WAL"),
) -> None:
    """Inspecciona los snapshots y la trayectoria histórica de una tarea en SQLite WAL."""
    checkpointer = SQLiteCheckpointService(db_path=db)
    snapshots = checkpointer.list_snapshots(task_id)

    if not snapshots:
        console.print(f"[yellow]No se encontraron snapshots para la tarea '{task_id}'.[/yellow]")
        return

    table = Table(title=f"Trayectoria de Snapshots: {task_id}", border_style="magenta")
    table.add_column("Paso", justify="right")
    table.add_column("Snapshot ID", style="cyan")
    table.add_column("Fase", style="green")
    table.add_column("Disyuntor", style="yellow")
    table.add_column("Timestamp", style="white")

    for s in snapshots:
        table.add_row(
            str(s.step_index),
            s.snapshot_id,
            s.phase.value,
            s.circuit_status.value,
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.timestamp)),
        )

    console.print(table)


@app.command()
def rollback(
    snapshot_id: str = typer.Argument(..., help="ID del snapshot hacia el cual rebobinar"),
    db: str = typer.Option("factory_checkpoints.db", "--db", help="Ruta de SQLite WAL"),
) -> None:
    """Time-travel debugging: rebobina el estado del grafo a un checkpoint histórico."""
    checkpointer = SQLiteCheckpointService(db_path=db)
    try:
        target = checkpointer.rollback_to(snapshot_id)
        console.print(
            f"[bold green]✔ Rollback exitoso:[/bold green] Estado restablecido a "
            f"[bold cyan]{target.snapshot_id}[/bold cyan] (Fase: {target.phase.value}, Paso {target.step_index})."
        )
    except Exception as exc:
        console.print(f"[bold red]Error en rollback:[/bold red] {exc}")


@app.command()
def telemetry(
    db: str = typer.Option("factory_checkpoints.db", "--db", help="Ruta de SQLite WAL"),
) -> None:
    """Muestra el panel consolidado de métricas AgentOps del entorno."""
    checkpointer = SQLiteCheckpointService(db_path=db)
    with checkpointer._get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*), phase FROM snapshots GROUP BY phase;")
        phase_counts = cursor.fetchall()
        total_cursor = conn.execute("SELECT COUNT(DISTINCT task_id) FROM snapshots;")
        total_tasks = total_cursor.fetchone()[0]

    table = Table(title="AgentOps & Telemetría Global del Entorno", border_style="blue")
    table.add_column("Métrica", style="bold white")
    table.add_column("Valor", style="bold cyan")

    table.add_row("Total Tareas Registradas", str(total_tasks))
    for count, phase in phase_counts:
        table.add_row(f"Snapshots en {phase}", str(count))

    console.print(table)


if __name__ == "__main__":
    app()
