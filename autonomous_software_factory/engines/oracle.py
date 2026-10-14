import re
import subprocess
import time
from autonomous_software_factory.domain.models import OracleResult


class DeterministicOracle:
    """
    Deterministic Truth Oracle enforcing EARS-U1:
    The system ALWAYS uses the subprocess exit code as the single source of truth,
    strictly ignoring any conversational or verbal assertions made by LLM agents.
    """

    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout

    def parse_output(
        self,
        exit_code: int,
        stdout: str,
        stderr: str = "",
        duration: float = 0.0,
        command: str = "pytest",
    ) -> OracleResult:
        """Parses test runner output into a strongly typed OracleResult."""
        passed = 0
        failed = 0

        # Extract passed count
        match_passed = re.search(r"(\d+)\s+passed", stdout)
        if match_passed:
            passed = int(match_passed.group(1))

        # Extract failed count
        match_failed = re.search(r"(\d+)\s+failed", stdout)
        if match_failed:
            failed = int(match_failed.group(1))

        return OracleResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
            passed_tests=passed,
            failed_tests=failed,
            command=command,
        )

    def execute_suite(
        self,
        cmd: list[str] | None = None,
        cwd: str | None = None,
        timeout: float | None = None,
    ) -> OracleResult:
        """Runs the test suite as an isolated subprocess and returns an OracleResult."""
        command = cmd or ["py", "-m", "pytest", "-q"]
        start_time = time.time()
        timeout_val = timeout or self.default_timeout

        try:
            process = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_val,
                check=False,
            )
            duration = time.time() - start_time
            return self.parse_output(
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration=duration,
                command=" ".join(command),
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.time() - start_time
            return OracleResult(
                exit_code=-1,
                stdout=exc.stdout or "",
                stderr=f"TimeoutExpired: test run exceeded {timeout_val}s",
                duration_seconds=duration,
                command=" ".join(command),
            )
        except Exception as exc:
            duration = time.time() - start_time
            return OracleResult(
                exit_code=255,
                stderr=str(exc),
                duration_seconds=duration,
                command=" ".join(command),
            )
