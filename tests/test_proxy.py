import httpx
import pytest


@pytest.fixture
def mock_upstream(mocker):
    """Mocks upstream HTTP calls made by the proxy without intercepting the ASGI test client."""
    mock_resp = httpx.Response(
        status_code=200,
        json={"balance": 1500},
        request=httpx.Request("POST", "https://api.internal/balance"),
    )
    mock_client = mocker.AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_resp

    mocker.patch(
        "agentguard.routes.proxy.httpx.AsyncClient", return_value=mock_client
    )
    return mock_client

@pytest.mark.asyncio
async def test_proxy_flow_and_caching(async_client, mock_upstream):
    payload = {
        "tool_name": "get_balance",
        "parameters": {"user_id": "u_123", "email": "test@test.com"},
        "upstream_url": "https://api.internal/balance",
    }

    # 1. Cache Miss
    resp1 = await async_client.post("/v1/execute", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["cached"] is False
    assert data1["sanitized"] is True
    assert data1["result"]["balance"] == 1500

    # 2. Cache Hit
    resp2 = await async_client.post("/v1/execute", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["cached"] is True
    assert data2["cache_key"] == data1["cache_key"]


@pytest.mark.asyncio
async def test_proxy_budget_throttling(async_client, mock_breaker, mock_upstream):
    mock_breaker.max_calls = 1

    payload = {
        "tool_name": "noop",
        "parameters": {},
        "upstream_url": "https://api.internal/noop",
    }

    res1 = await async_client.post("/v1/execute", json=payload)
    assert res1.status_code == 200

    res2 = await async_client.post("/v1/execute", json=payload)
    assert res2.status_code == 429
    assert "budget exceeded" in res2.json()["detail"]

@pytest.mark.asyncio
async def test_proxy_upstream_failure_returns_502(async_client, mocker):
    mock_client = mocker.AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = httpx.ConnectError("Connection refused by upstream target")

    mocker.patch("agentguard.routes.proxy.httpx.AsyncClient", return_value=mock_client)

    payload = {
        "tool_name": "network_tool",
        "parameters": {},
        "upstream_url": "https://offline.upstream.service/api",
    }

    response = await async_client.post("/v1/execute", json=payload)
    assert response.status_code == 502
    assert "Upstream provider failure" in response.json()["detail"]

@pytest.mark.asyncio
async def test_health_check_endpoint(async_client):
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"