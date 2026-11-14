import json
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from agentguard.hasher import compute_tool_hash
from agentguard.middleware.budget import BudgetCircuitBreaker
from agentguard.middleware.sanitizer import sanitize_payload
from agentguard.models import ToolCallRequest, ToolCallResponse
from agentguard.storage.base import BaseCacheStorage

router = APIRouter(prefix="/v1", tags=["Proxy"])


def get_storage() -> BaseCacheStorage:
    raise NotImplementedError


def get_budget_breaker() -> BudgetCircuitBreaker:
    raise NotImplementedError


@router.post("/execute", response_model=ToolCallResponse)
async def execute_tool(
    request: ToolCallRequest,
    storage: BaseCacheStorage = Depends(get_storage),
    breaker: BudgetCircuitBreaker = Depends(get_budget_breaker),
) -> ToolCallResponse:
    start_time = time.perf_counter()

    # 1. Check budget circuit breaker
    if not breaker.record_and_check():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Agent loop budget exceeded. Execution throttled to prevent runaway billing.",
        )

    # 2. Scrub sensitive data
    sanitized_params, was_sanitized = sanitize_payload(request.parameters)

    # 3. Compute deterministic fingerprint
    cache_key = compute_tool_hash(request.tool_name, sanitized_params)
    ttl = request.ttl_seconds or 3600

    # 4. Check cache hit
    cached_val = await storage.get(cache_key)
    if cached_val is not None:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return ToolCallResponse(
            tool_name=request.tool_name,
            result=json.loads(cached_val),
            cached=True,
            execution_time_ms=round(elapsed_ms, 2),
            cache_key=cache_key,
            sanitized=was_sanitized,
        )

    # 5. Upstream execution on cache miss
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(request.upstream_url, json=sanitized_params)
            resp.raise_for_status()
            upstream_data = resp.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Upstream provider failure: {exc!s}",
            ) from exc

    # 6. Store in cache
    await storage.set(cache_key, json.dumps(upstream_data), ttl_seconds=ttl)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return ToolCallResponse(
        tool_name=request.tool_name,
        result=upstream_data,
        cached=False,
        execution_time_ms=round(elapsed_ms, 2),
        cache_key=cache_key,
        sanitized=was_sanitized,
    )
