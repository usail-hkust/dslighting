"""Content-addressed storage for debug payloads."""

from __future__ import annotations

import hashlib
import json
from itertools import count
from pathlib import Path
from typing import Any

from dslighting.debug.models import PayloadRef
from dslighting.debug.redaction import RedactionPolicy


class PayloadStore:
    def __init__(
        self,
        *,
        output_dir: Path | None,
        redaction_policy: RedactionPolicy,
        dedupe_enabled: bool = True,
    ) -> None:
        self.output_dir = output_dir
        self.redaction_policy = redaction_policy
        self.dedupe_enabled = dedupe_enabled
        self._seq = count(1)
        self._payloads_by_ref: dict[str, Any] = {}
        self._refs_by_hash: dict[tuple[str, str], str] = {}

    def store(self, *, kind: str, body: Any) -> PayloadRef:
        redacted_body = self.redaction_policy.redact_any(body)
        canonical = self._canonicalize(redacted_body)
        sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        key = (kind, sha256)
        if self.dedupe_enabled and key in self._refs_by_hash:
            ref = self._refs_by_hash[key]
            return self._build_ref(ref, kind, sha256, canonical, redacted_body, reused=True)

        ref = f"{kind}_{next(self._seq):05d}_{sha256[:8]}"
        self._refs_by_hash[key] = ref
        self._payloads_by_ref[ref] = redacted_body
        return self._build_ref(ref, kind, sha256, canonical, redacted_body, reused=False)

    def get(self, ref: str) -> Any:
        return self._payloads_by_ref[ref]

    def flush(self) -> None:
        return None

    @staticmethod
    def _canonicalize(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    def _build_ref(
        self,
        ref: str,
        kind: str,
        sha256: str,
        canonical: str,
        body: Any,
        *,
        reused: bool,
    ) -> PayloadRef:
        payload_bytes = canonical.encode("utf-8")
        return PayloadRef(
            ref=ref,
            sha256=sha256,
            kind=kind,
            bytes_len=len(payload_bytes),
            chars_len=len(canonical),
            reused=reused,
            preview=self._preview(body),
        )

    @staticmethod
    def _preview(body: Any) -> str:
        if isinstance(body, str):
            text = body.strip()
        else:
            text = json.dumps(body, ensure_ascii=False, sort_keys=True, default=str)
        text = " ".join(text.split())
        return text[:120] + ("..." if len(text) > 120 else "")
