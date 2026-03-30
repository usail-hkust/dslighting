from __future__ import annotations

from pathlib import Path


README_EXPECTED_TOKENS = (
    "class AgentResult:",
    "success: bool",
    "output: Any",
    "cost: float = 0.0",
    "duration: float = 0.0",
    "score: float | None = None",
    "artifacts_path: Path | None = None",
    "workspace_path: Path | None = None",
    "error: str | None = None",
    "metadata: dict[str, Any] = field(default_factory=dict)",
)


def test_readme_agentresult_signature_matches_core_interface() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    for token in README_EXPECTED_TOKENS:
        assert token in text


