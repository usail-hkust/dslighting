from __future__ import annotations

from dslighting.debug.payload_store import PayloadStore
from dslighting.debug.redaction import RedactionPolicy


def test_payload_store_dedupes_and_redacts_secrets() -> None:
    store = PayloadStore(output_dir=None, redaction_policy=RedactionPolicy(), dedupe_enabled=True)

    first = store.store(
        kind="request_messages",
        body={
            "api_key": "super-secret",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    second = store.store(
        kind="request_messages",
        body={
            "api_key": "super-secret",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert first.ref == second.ref
    assert first.reused is False
    assert second.reused is True
    assert store.get(first.ref)["api_key"] == "***REDACTED***"
