from contextlib import asynccontextmanager

from fastapi import FastAPI

from agentguard.config import settings
from agentguard.middleware.budget import BudgetCircuitBreaker
from agentguard.routes import proxy
from agentguard.storage.memory import InMemoryCacheStorage


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage = InMemoryCacheStorage()
    breaker = BudgetCircuitBreaker(max_calls_per_window=settings.budget_limit_per_minute)
    app.dependency_overrides[proxy.get_storage] = lambda: storage
    app.dependency_overrides[proxy.get_budget_breaker] = lambda: breaker
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Safety and caching reverse-proxy for autonomous LLM tool executions",
    lifespan=lifespan,
)

app.include_router(proxy.router)


@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "agentguard"}
