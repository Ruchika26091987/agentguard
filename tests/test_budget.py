from agentguard.middleware.budget import BudgetCircuitBreaker


def test_circuit_breaker_trips():
    breaker = BudgetCircuitBreaker(max_calls_per_window=2, window_seconds=10.0)
    assert breaker.record_and_check() is True
    assert breaker.record_and_check() is True
    # 3rd call exceeds budget
    assert breaker.record_and_check() is False


def test_circuit_breaker_resets():
    breaker = BudgetCircuitBreaker(max_calls_per_window=1, window_seconds=10.0)
    assert breaker.record_and_check() is True
    assert breaker.record_and_check() is False
    breaker.reset()
    assert breaker.record_and_check() is True
