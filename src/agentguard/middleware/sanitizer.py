import re
from typing import Any, Tuple

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
BEARER_TOKEN_REGEX = re.compile(r"(?i)\b(bearer\s+[a-zA-Z0-9_\-\.]{15,})\b")


def sanitize_payload(data: Any) -> Tuple[Any, bool]:
    """Recursively walks nested structures and redacts PII/tokens."""
    modified = False

    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            scrubbed_v, sub_modified = sanitize_payload(v)
            new_dict[k] = scrubbed_v
            if sub_modified:
                modified = True
        return new_dict, modified

    if isinstance(data, list):
        new_list = []
        for item in data:
            scrubbed_item, sub_modified = sanitize_payload(item)
            new_list.append(scrubbed_item)
            if sub_modified:
                modified = True
        return new_list, modified

    if isinstance(data, str):
        val = data
        if EMAIL_REGEX.search(val):
            val = EMAIL_REGEX.sub("[REDACTED_EMAIL]", val)
            modified = True
        if CREDIT_CARD_REGEX.search(val):
            val = CREDIT_CARD_REGEX.sub("[REDACTED_CC]", val)
            modified = True
        if BEARER_TOKEN_REGEX.search(val):
            val = BEARER_TOKEN_REGEX.sub("[REDACTED_TOKEN]", val)
            modified = True
        return val, modified

    return data, False
