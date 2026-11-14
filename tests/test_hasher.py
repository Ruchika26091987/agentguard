from agentguard.hasher import compute_tool_hash


def test_hash_key_order_invariance():
    payload_1 = {"b": 20, "a": 10, "nested": {"y": 2, "x": 1}}
    payload_2 = {"a": 10, "b": 20, "nested": {"x": 1, "y": 2}}

    hash_1 = compute_tool_hash("query_db", payload_1)
    hash_2 = compute_tool_hash("query_db", payload_2)
    assert hash_1 == hash_2


def test_hash_distinguishes_different_inputs():
    hash_base = compute_tool_hash("tool_a", {"val": 1})
    hash_diff_val = compute_tool_hash("tool_a", {"val": 2})
    hash_diff_tool = compute_tool_hash("tool_b", {"val": 1})

    assert hash_base != hash_diff_val
    assert hash_base != hash_diff_tool
