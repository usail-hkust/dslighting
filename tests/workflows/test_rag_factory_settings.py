from __future__ import annotations

import pytest

from dslighting.config import DSLightingConfig, WorkflowConfig
from dslighting.error import ConfigurationError
from dslighting.workflows.factory.builtin import _resolve_rag_settings


def test_resolve_rag_settings_default_values() -> None:
    config = DSLightingConfig(workflow=WorkflowConfig(name="dsagent", params={}))
    enable_rag, case_dir = _resolve_rag_settings(config, "dsagent")
    assert enable_rag is True
    assert case_dir == "experience_replay"


def test_resolve_rag_settings_rejects_invalid_enable_rag() -> None:
    config = DSLightingConfig(workflow=WorkflowConfig(name="dsagent", params={"enable_rag": "yes"}))
    with pytest.raises(ConfigurationError, match="enable_rag"):
        _resolve_rag_settings(config, "dsagent")


def test_resolve_rag_settings_rejects_invalid_case_dir() -> None:
    config = DSLightingConfig(workflow=WorkflowConfig(name="dsagent", params={"case_dir": ""}))
    with pytest.raises(ConfigurationError, match="case_dir"):
        _resolve_rag_settings(config, "dsagent")
