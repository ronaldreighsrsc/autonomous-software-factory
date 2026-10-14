import pytest
from autonomous_software_factory.domain.models import OracleResult
from autonomous_software_factory.engines.oracle import DeterministicOracle
from autonomous_software_factory.engines.reflexion import ReflexionEngine


def test_oracle_parses_pytest_summary_output():
    oracle = DeterministicOracle()
    output_sample = """
============================= test session starts =============================
tests/test_calc.py .F.
================================== FAILURES ===================================
_________________________________ test_divide _________________________________
    def test_divide():
>       assert divide(10, 2) == 4
E       AssertionError: assert 5 == 4
tests/test_calc.py:6: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_calc.py::test_divide - AssertionError: assert 5 == 4
========================= 1 failed, 2 passed in 0.12s =========================
"""
    result = oracle.parse_output(exit_code=1, stdout=output_sample, stderr="", duration=0.12)
    assert result.exit_code == 1
    assert result.is_success is False
    assert result.passed_tests == 2
    assert result.failed_tests == 1
    assert result.duration_seconds == 0.12


def test_oracle_strictly_rejects_verbal_success_if_exit_code_non_zero():
    oracle = DeterministicOracle()
    # LLM might produce a message claiming "All tests passed successfully!" but if exit_code is 1:
    verbal_claim = "All 10 tests passed completely! 100% green!"
    result = oracle.parse_output(exit_code=2, stdout=verbal_claim, stderr="SyntaxError in foo.py", duration=0.05)
    assert result.is_success is False
    assert result.exit_code == 2


def test_reflexion_engine_sanitizes_stacktrace():
    reflexion = ReflexionEngine()
    raw_error = """
============================= test session starts =============================
platform win32 -- Python 3.12.2, pytest-8.1.1, pluggy-1.4.0
rootdir: C:\\Users\\ronal\\test
collected 1 item

tests/test_foo.py F                                                      [100%]

================================== FAILURES ===================================
__________________________________ test_fail __________________________________
    def test_fail():
>       assert calculate_margin(100, 50) == 0.6
E       assert 0.5 == 0.6
tests/test_foo.py:12: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_foo.py::test_fail - assert 0.5 == 0.6
============================== 1 failed in 0.05s ==============================
"""
    feedback = reflexion.build_corrective_observation(raw_error)
    assert "assert 0.5 == 0.6" in feedback
    # Noise like platform and rootdir should be filtered out
    assert "platform win32" not in feedback
    assert "rootdir:" not in feedback
    assert "OBSERVACIÓN DEL ORÁCULO" in feedback
