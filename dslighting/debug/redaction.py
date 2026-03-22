"""Redaction helpers for debug payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_REDACTED = "***REDACTED***"
_SECRET_KEYS = {
    "api_key",
    "api_keys",
    "authorization",
    "token",
    "access_token",
    "secret",
    "password",
    "cookie",
}


class RedactionPolicy:
    """Redact obviously sensitive values before they are persisted."""

    def redact_mapping(self, value: Mapping[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in _SECRET_KEYS:
                redacted[key] = _REDACTED
            else:
                redacted[key] = self.redact_any(item)
        return redacted

    def redact_any(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return self.redact_mapping(value)
        if isinstance(value, (list, tuple)):
            return [self.redact_any(item) for item in value]
        if isinstance(value, set):
            return [self.redact_any(item) for item in sorted(value, key=repr)]
        return value
