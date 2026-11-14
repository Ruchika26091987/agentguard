from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolCallRequest(BaseModel):
    tool_name: str = Field(..., description="Target tool or function identifier")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Invocation arguments")
    upstream_url: str = Field(..., description="Target API endpoint on cache miss")
    ttl_seconds: Optional[int] = Field(None, ge=1, description="Optional custom cache TTL")


class ToolCallResponse(BaseModel):
    tool_name: str
    result: Any
    cached: bool
    execution_time_ms: float
    cache_key: str
    sanitized: bool = False
