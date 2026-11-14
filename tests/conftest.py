import pytest
from httpx import ASGITransport, AsyncClient

from agentguard.main import app
from agentguard.middleware.budget import BudgetCircuitBreaker
from agentguard.routes.proxy import get_budget_breaker, get_storage
from agentguard.storage.memory import InMemoryCacheStorage


@pytest.fixture
def mock_storage():
    return InMemoryCacheStorage()


@pytest.fixture
def mock_breaker():
    return BudgetCircuitBreaker(max_calls_per_window=5, window_seconds=60.0)


@pytest.fixture
async def async_client(mock_storage, mock_breaker):
    app.dependency_overrides[get_storage] = lambda: mock_storage
    app.dependency_overrides[get_budget_breaker] = lambda: mock_breaker
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()
