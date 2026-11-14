AgentGuard 🛡️

High-performance async runtime safety and deterministic caching gateway for autonomous LLM tool executions.

Autonomous AI agents frequently trigger repetitive deterministic API calls (e.g., docs search, schema queries, read-only database reads), leak sensitive credentials, or enter runaway execution loops that rapidly drain API budgets. AgentGuard sits inline as a zero-trust reverse-proxy between agent runtimes (Claude Code, LangChain, AutoGen, custom agent loops) and external tools/APIs—enforcing budget circuit breakers, scrubbing PII, and caching results via canonical SHA-256 fingerprinting in under 2ms.

Architecture Overview

┌────────────────────┐     HTTP / JSON      ┌─────────────────────────────┐
│  AI Agent Runtime  │ ───────────────────> │     AgentGuard Gateway      │
│(Claude, LangChain) │ <─────────────────── │   (FastAPI + Sanitizer)     │
└────────────────────┘     Cached (<2ms)    └──────────────┬──────────────┘
                                                           │
                                   ┌───────────────────────┴───────────────────────┐
                                   ▼                                               ▼
                         [Cache Hit: Memory/Redis]                      [Cache Miss: Forward]
                         Returns cached payload                         Calls Upstream API


Request Flow

Loop Guard: Sliding-window circuit breaker checks invocation frequency, returning 429 Too Many Requests if the safety budget is exceeded.

PII Sanitizer: Recursively walks tool arguments to scrub emails, credit card patterns, and bearer tokens before network transmission.

Deterministic Hasher: Serializes parameters into key-sorted canonical JSON to guarantee identical SHA-256 hashes regardless of dictionary key ordering.

Cache Lookup: Returns cached JSON payloads in <2ms on a hit.

Upstream Forwarding: Dispatches cache misses to upstream targets using an async HTTP client (httpx), persists responses, and applies custom TTL boundaries.

Key Features

Deterministic Parameter Hashing: Canonical JSON serialization normalizes argument dictionaries and nested arrays, ensuring order-invariant cache keys.

Runaway Loop Protection: Sliding-window circuit breaker (BudgetCircuitBreaker) prevents infinite agent loops from exhausting downstream API budgets.

In-Flight Data Sanitization: Recursively identifies and redacts sensitive PII (emails, payment cards, bearer tokens) before payload serialization or forwarding.

Pluggable Storage Layer: Abstract base interface with an in-memory TTL implementation for local testing and interface contracts ready for distributed Redis clusters.

High Test Quality: >90% test coverage with asynchronous ASGI mock fixtures, error boundary tests, and zero external network dependencies in CI.

Directory Layout

agentguard/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated Ruff linting and Pytest with coverage gate
├── src/
│   └── agentguard/
│       ├── __init__.py          # Package metadata
│       ├── config.py            # Pydantic v2 settings & environment variables
│       ├── main.py              # FastAPI application lifecycle and routes
│       ├── models.py            # Pydantic schemas (ToolCallRequest, ToolCallResponse)
│       ├── hasher.py            # Canonical JSON serializer & SHA-256 fingerprint engine
│       ├── storage/
│       │   ├── base.py          # Abstract Base Class for cache backends
│       │   └── memory.py        # In-memory TTL backend with expiring dict
│       ├── middleware/
│       │   ├── budget.py        # Sliding-window invocation budget circuit breaker
│       │   └── sanitizer.py     # Recursive PII & token redaction middleware
│       └── routes/
│           └── proxy.py         # Async reverse-proxy endpoint (/v1/execute)
├── tests/
│   ├── conftest.py              # Asynchronous test client and mock fixtures
│   ├── test_budget.py           # Unit tests for sliding-window limits and resets
│   ├── test_hasher.py           # Key-order invariance and collision resistance tests
│   ├── test_proxy.py            # Cache hit/miss and upstream error handling integration tests
│   ├── test_sanitizer.py        # PII and bearer token redaction unit tests
│   └── test_storage.py          # Memory storage TTL expiration and pattern purge tests
├── pyproject.toml               # Modern build specification (Hatchling, Ruff, Pytest)
├── README.md
└── TODO.md                      # Active development roadmap


Tech Stack

Language & Framework: Python 3.11+, FastAPI, Uvicorn

Data Validation & Settings: Pydantic v2, Pydantic-Settings

Networking & Transport: HTTPX (async client with timeout policies)

Storage & Caching: Redis (redis-py async engine) with an in-memory TTL fallback

Quality Assurance: Pytest, Pytest-Asyncio, Pytest-Mock, Coverage (>90%), Ruff

Quickstart

1. Clone & Set Up Environment

# Clone the repository
git clone https://github.com/Ruchika26091987/agentguard.git
cd agentguard

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"


2. Run Test Suite

pytest


3. Launch the Gateway

uvicorn agentguard.main:app --host 0.0.0.0 --port 8080 --reload


Verify service health:

curl http://localhost:8080/healthz
# Response: {"status":"healthy","service":"agentguard"}


Usage Example

Send an agent tool execution payload through the proxy:

curl -X POST http://localhost:8080/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "query_customer_db",
    "parameters": {
      "customer_id": "cust_1111",
      "email": "user@example.com"
    },
    "upstream_url": "https://httpbin.org/post",
    "ttl_seconds": 300
  }'


First Request: cached: false (Executes upstream, sanitizes PII, and stores in cache).

Second Request: cached: true (Served in <2ms directly from cache; upstream bypassed).

Active Roadmap & Open Issues

[ ] Issue #1: feat(storage): Implement async Redis storage driver with connection pooling and retry backoff.

[ ] Issue #2: feat(telemetry): Export Prometheus /metrics endpoint for cache hit ratio and latency percentiles.

[ ] Issue #3: feat(policy): Add dynamic YAML policy loading for custom per-tool TTLs and bypass rules.

[ ] Issue #4: feat(streaming): Add Server-Sent Events (SSE) proxy support for long-running generative agent tools.


