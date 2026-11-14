from agentguard.middleware.sanitizer import sanitize_payload


def test_sanitizes_emails_and_cards():
    input_data = {
        "user": "test",
        "email": "test@example.com",
        "card": "4111 2222 3333 4444",
        "notes": ["Send report to test@example.com"],
    }
    sanitized, modified = sanitize_payload(input_data)
    assert modified is True
    assert sanitized["email"] == "[REDACTED_EMAIL]"
    assert sanitized["card"] == "[REDACTED_CC]"
    assert sanitized["notes"][0] == "Send report to [REDACTED_EMAIL]"


def test_clean_payload_untouched():
    clean_data = {"tool": "calculator", "op": "add", "args": [1, 2]}
    sanitized, modified = sanitize_payload(clean_data)
    assert modified is False
    assert sanitized == clean_data

def test_sanitizes_bearer_tokens():
    raw_payload = {"headers": {"Authorization": "Bearer abc123def456ghi789jkl0"}}
    cleaned, modified = sanitize_payload(raw_payload)
    assert modified is True
    assert "[REDACTED_TOKEN]" in cleaned["headers"]["Authorization"]