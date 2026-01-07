"""
Persistent library for discovered operators.

This stores LLM-proposed Operator code + metadata across runs, and tracks basic
usage/success statistics to support simple operator-level selection.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


@dataclass(frozen=True)
class LibraryOperatorSpec:
    name: str
    version: int
    code: str
    description: str
    inputs: str
    outputs: str
    triggers: str
    task_types: List[str]
    uses: int
    successes: int
    failures: int


class OperatorLibrary:
    def __init__(self, path: Path):
        self.path = path
        self._data: Dict[str, Any] = {"operators": {}}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._data = {"operators": {}}
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self._data = {"operators": {}}
            return

        if not isinstance(payload, dict) or not isinstance(payload.get("operators"), dict):
            self._data = {"operators": {}}
            return
        self._data = payload

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    def has(self, name: str) -> bool:
        return name in self._data.get("operators", {})

    def get_best_version(self, name: str) -> Optional[LibraryOperatorSpec]:
        """
        Return the best available version for an operator name.

        Selection is based on (success_rate, uses, version) in descending order.
        Returns None if the operator is missing or has no usable versions.
        """
        operators = self._data.get("operators", {})
        if not isinstance(operators, dict):
            return None

        record = operators.get(name)
        if not isinstance(record, dict):
            return None
        versions = record.get("versions", [])
        if not isinstance(versions, list) or not versions:
            return None

        best: Optional[Dict[str, Any]] = None
        best_key: Optional[tuple[float, int, int]] = None
        best_version = 1

        for v in versions:
            if not isinstance(v, dict):
                continue
            code = str(v.get("code") or "")
            if not code.strip():
                continue
            uses = _safe_int(v.get("uses"), 0)
            successes = _safe_int(v.get("successes"), 0)
            version = _safe_int(v.get("version"), 1)
            success_rate = successes / uses if uses > 0 else 0.0
            key = (float(success_rate), int(uses), int(version))
            if best_key is None or key > best_key:
                best = v
                best_key = key
                best_version = version

        if best is None:
            return None

        return LibraryOperatorSpec(
            name=str(name),
            version=int(best_version),
            code=str(best.get("code") or ""),
            description=str(best.get("description") or "").strip(),
            inputs=str(best.get("inputs") or "").strip(),
            outputs=str(best.get("outputs") or "").strip(),
            triggers=str(best.get("triggers") or "").strip(),
            task_types=list(best.get("task_types") or []),
            uses=_safe_int(best.get("uses"), 0),
            successes=_safe_int(best.get("successes"), 0),
            failures=_safe_int(best.get("failures"), 0),
        )

    def add_version(
        self,
        name: str,
        *,
        code: str,
        description: str,
        inputs: str = "",
        outputs: str = "",
        triggers: str = "",
        task_types: Optional[Iterable[str]] = None,
    ) -> int:
        operators = self._data.setdefault("operators", {})
        record = operators.setdefault(name, {"versions": []})
        versions: List[Dict[str, Any]] = record.setdefault("versions", [])

        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]
        for v in versions:
            if v.get("code_hash") == code_hash:
                return _safe_int(v.get("version"), default=1)

        next_version = 1 + max((_safe_int(v.get("version"), 0) for v in versions), default=0)
        versions.append(
            {
                "version": next_version,
                "code_hash": code_hash,
                "code": code,
                "description": (description or "").strip(),
                "inputs": (inputs or "").strip(),
                "outputs": (outputs or "").strip(),
                "triggers": (triggers or "").strip(),
                "task_types": [t for t in (task_types or []) if isinstance(t, str) and t.strip()],
                "created_at": _utc_now_iso(),
                "uses": 0,
                "successes": 0,
                "failures": 0,
                "seen_competition_ids": [],
            }
        )
        self._save()
        return next_version

    def record_outcome(
        self,
        name: str,
        version: int,
        *,
        success: bool,
        competition_ids: Optional[Iterable[str]] = None,
    ) -> None:
        operators = self._data.get("operators", {})
        record = operators.get(name)
        if not isinstance(record, dict):
            return
        versions = record.get("versions", [])
        if not isinstance(versions, list):
            return

        for v in versions:
            if _safe_int(v.get("version"), -1) != int(version):
                continue
            v["uses"] = _safe_int(v.get("uses"), 0) + 1
            if success:
                v["successes"] = _safe_int(v.get("successes"), 0) + 1
                v["last_success_at"] = _utc_now_iso()
            else:
                v["failures"] = _safe_int(v.get("failures"), 0) + 1
            v["last_used_at"] = _utc_now_iso()

            if competition_ids:
                seen = set(v.get("seen_competition_ids") or [])
                for cid in competition_ids:
                    if isinstance(cid, str) and cid:
                        seen.add(cid)
                v["seen_competition_ids"] = sorted(seen)

            self._save()
            return

    def select_for_prompt(
        self,
        max_ops: int,
        *,
        competition_ids: Optional[Iterable[str]] = None,
        task_types: Optional[Iterable[str]] = None,
    ) -> List[LibraryOperatorSpec]:
        """
        Select up to `max_ops` operators (best version per operator) using a simple UCB score.
        Adds a small bonus when an operator has succeeded on the same competition_ids or task_types.
        """
        operators = self._data.get("operators", {})
        if not isinstance(operators, dict) or max_ops <= 0:
            return []

        preferred_competitions = {
            cid for cid in (competition_ids or []) if isinstance(cid, str) and cid.strip()
        }
        preferred_task_types = {
            t.strip().lower() for t in (task_types or []) if isinstance(t, str) and t.strip()
        }

        all_versions: List[Tuple[str, Dict[str, Any]]] = []
        for name, record in operators.items():
            if not isinstance(record, dict):
                continue
            for v in record.get("versions", []) or []:
                if isinstance(v, dict):
                    all_versions.append((name, v))

        total_uses = sum(_safe_int(v.get("uses"), 0) for _, v in all_versions)
        total_uses = max(1, total_uses)

        best_by_name: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        for name, v in all_versions:
            uses = _safe_int(v.get("uses"), 0)
            successes = _safe_int(v.get("successes"), 0)
            mean = successes / max(1, uses)
            ucb = mean + math.sqrt(2.0 * math.log(total_uses + 1.0) / (uses + 1.0))

            bonus = 0.0
            if preferred_competitions:
                seen = {c for c in (v.get("seen_competition_ids") or []) if isinstance(c, str) and c}
                if seen & preferred_competitions:
                    bonus += 0.25
            if preferred_task_types:
                vtypes = {
                    t.strip().lower()
                    for t in (v.get("task_types") or [])
                    if isinstance(t, str) and t.strip()
                }
                if vtypes & preferred_task_types:
                    bonus += 0.15

            score = ucb + bonus
            prev = best_by_name.get(name)
            if prev is None or score > prev[0]:
                best_by_name[name] = (score, v)

        ranked = sorted(best_by_name.items(), key=lambda kv: kv[1][0], reverse=True)
        selected = ranked[:max_ops]

        specs: List[LibraryOperatorSpec] = []
        for name, (_score, v) in selected:
            specs.append(
                LibraryOperatorSpec(
                    name=name,
                    version=_safe_int(v.get("version"), 1),
                    code=str(v.get("code") or ""),
                    description=str(v.get("description") or "").strip(),
                    inputs=str(v.get("inputs") or "").strip(),
                    outputs=str(v.get("outputs") or "").strip(),
                    triggers=str(v.get("triggers") or "").strip(),
                    task_types=list(v.get("task_types") or []),
                    uses=_safe_int(v.get("uses"), 0),
                    successes=_safe_int(v.get("successes"), 0),
                    failures=_safe_int(v.get("failures"), 0),
                )
            )
        return specs
