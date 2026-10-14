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
