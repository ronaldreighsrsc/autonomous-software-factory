import pytest
from autonomous_software_factory.domain.models import CircuitStatus
from autonomous_software_factory.engines.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerTrippedError,
)


def test_circuit_breaker_trips_on_consecutive_identical_tool_calls():
    cb = CircuitBreaker()
    # First call: valid
    cb.verify_safety("run_test", {"path": "tests/test_foo.py"})
    assert cb.status == CircuitStatus.OK

    # Different call: valid
    cb.verify_safety("edit_file", {"path": "foo.py", "content": "x = 1"})
    assert cb.status == CircuitStatus.OK

    # Repeat exact same call consecutively: TRIPS
    with pytest.raises(CircuitBreakerTrippedError) as exc_info:
        cb.verify_safety("edit_file", {"path": "foo.py", "content": "x = 1"})

    assert exc_info.value.status == CircuitStatus.TRIPPED_OSCILLATION
    assert cb.status == CircuitStatus.TRIPPED_OSCILLATION
    assert "Anti-oscillation triggered" in str(exc_info.value)


def test_circuit_breaker_trips_on_max_steps():
    cb = CircuitBreaker(max_steps=3)
    cb.record_step()
    cb.record_step()
    cb.record_step()
    assert cb.status == CircuitStatus.OK

    # 4th step exceeds max_steps=3
    with pytest.raises(CircuitBreakerTrippedError) as exc_info:
        cb.record_step()

    assert exc_info.value.status == CircuitStatus.TRIPPED_STEPS
    assert cb.status == CircuitStatus.TRIPPED_STEPS


def test_circuit_breaker_trips_on_budget_exceeded():
    cb = CircuitBreaker(max_cost_usd=0.10)
    cb.record_step(additional_cost=0.06)
    assert cb.status == CircuitStatus.OK

    with pytest.raises(CircuitBreakerTrippedError) as exc_info:
        cb.record_step(additional_cost=0.05)  # Total 0.11 > 0.10

    assert exc_info.value.status == CircuitStatus.TRIPPED_COST
    assert cb.status == CircuitStatus.TRIPPED_COST


def test_circuit_breaker_thought_recording():
    cb = CircuitBreaker()
    cb.record_thought("Analyzing root cause in parser.py")
    assert len(cb.thoughts) == 1
    assert "parser.py" in cb.thoughts[0]


def test_circuit_breaker_trips_on_test_tampering_in_green_phase():
    cb = CircuitBreaker()
    cb.lock_test_suite({"tests/test_foo.py": "def test_a():\n    assert 1 + 1 == 2\n"})

    # 1. Editing production code in green phase is allowed
    cb.verify_safety("edit_file", {"path": "src/foo.py", "content": "return 2"})
    assert cb.status == CircuitStatus.OK

    # 2. Attempting to edit a locked test file during green/fixer phase trips TRIPPED_TEST_TAMPERING
    with pytest.raises(CircuitBreakerTrippedError) as exc_info:
        cb.verify_safety("edit_file", {"path": "tests/test_foo.py", "content": "assert True"})

    assert exc_info.value.status == CircuitStatus.TRIPPED_TEST_TAMPERING
    assert cb.status == CircuitStatus.TRIPPED_TEST_TAMPERING

    # 3. Direct cryptographic hash integrity check also detects external tampering
    cb2 = CircuitBreaker()
    cb2.lock_test_suite({"tests/test_foo.py": "def test_a():\n    assert 1 + 1 == 2\n"})
    with pytest.raises(CircuitBreakerTrippedError) as exc_hash:
        cb2.verify_test_integrity({"tests/test_foo.py": "def test_a():\n    assert True\n"})
    assert exc_hash.value.status == CircuitStatus.TRIPPED_TEST_TAMPERING


def test_circuit_breaker_trips_on_blast_radius_exceeded():
    cb = CircuitBreaker(max_files_per_step=3, max_diff_lines=100)
    # 3 files and 60 lines -> within Vertical Slice budget
    assert cb.verify_blast_radius(modified_files=["a.py", "b.py", "c.py"], diff_lines=60) is True
    assert cb.status == CircuitStatus.OK

    # 4 files -> exceeds Vertical Slice file limit (max 3)
    with pytest.raises(CircuitBreakerTrippedError) as exc_files:
        cb.verify_blast_radius(modified_files=["a.py", "b.py", "c.py", "d.py"], diff_lines=60)
    assert exc_files.value.status == CircuitStatus.TRIPPED_BLAST_RADIUS
    assert cb.status == CircuitStatus.TRIPPED_BLAST_RADIUS

