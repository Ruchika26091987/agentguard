import hashlib
import json
from typing import Any, Dict


def canonicalize(data: Any) -> Any:
    """Recursively sorts nested dictionaries for deterministic hashing."""
    if isinstance(data, dict):
        return {k: canonicalize(v) for k, v in sorted(data.items())}
    if isinstance(data, list):
        return [canonicalize(i) for i in data]
    return data


def compute_tool_hash(tool_name: str, parameters: Dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 fingerprint for a tool call invocation."""
    canonical_data = canonicalize(parameters)
    serialized = json.dumps(canonical_data, separators=(",", ":"), default=str)
    raw_key = f"{tool_name}:{serialized}".encode()
    return hashlib.sha256(raw_key).hexdigest()
