from __future__ import annotations

from dslighting.config import DSLightingConfig
from dslighting.core import ConfigBuilder
from dslighting.core.application.agent_config_builder import AgentConfigBuilder
from dslighting.services.data_analysis_provider import (
    create_data_analyzer,
    create_data_perception_runtime,
)


def _make_agent_builder(init_kwargs: dict) -> AgentConfigBuilder:
    return AgentConfigBuilder(
        workflow_name="aide",
        model="gpt-4o",
        api_key=None,
        api_keys=None,
        api_base=None,
        provider=None,
        temperature=None,
        timeout=300,
        keep_workspace=False,
        sandbox_backend=None,
        sandbox_backend_type=None,
        sandbox_timeout=None,
        sandbox_api_key=None,
        init_kwargs=init_kwargs,
    )


def test_build_config_accepts_data_analysis_block() -> None:
    config = ConfigBuilder().build_config(
        model="model-a",
        data_analysis={
            "cache_enabled": False,
            "cache_dir": "/tmp/dslighting-cache",
            "cache_max_entries": 32,
        },
    )

    assert config.data_analysis.enabled is True
    assert config.data_analysis.cache_enabled is False
    assert config.data_analysis.cache_dir == "/tmp/dslighting-cache"
    assert config.data_analysis.cache_max_entries == 32


def test_agent_config_builder_applies_data_analysis_from_runtime_kwargs() -> None:
    builder = _make_agent_builder(init_kwargs={})
    config = builder.build(
        task_id="task1",
        run_kwargs={"data_analysis": {"cache_enabled": False, "cache_debug_metrics": True}},
    )

    assert config.data_analysis.cache_enabled is False
    assert config.data_analysis.cache_debug_metrics is True


def test_create_data_analyzer_respects_disabled_flag() -> None:
    config = DSLightingConfig.model_validate({"data_analysis": {"enabled": False}})

    analyzer = create_data_analyzer(config)
    runtime = create_data_perception_runtime(config)

    assert analyzer is None
    assert runtime is None


def test_create_data_analyzer_applies_extended_runtime_settings() -> None:
    config = DSLightingConfig.model_validate(
        {
            "data_analysis": {
                "profile": "full",
                "max_artifacts": 20,
                "max_report_chars": 9000,
                "document_preview_lines": 5,
                "enable_document_inspection": True,
                "enable_database_inspection": False,
                "tabular_tolerant_fallback": False,
            }
        }
    )

    analyzer = create_data_analyzer(config)

    assert analyzer is not None
    assert analyzer.profile == "full"
    assert analyzer.max_artifacts == 20
    assert analyzer.max_report_chars == 9000
    assert analyzer.document_preview_lines == 5
    assert analyzer.enable_document_inspection is True
    assert analyzer.enable_database_inspection is False
    assert analyzer.tabular_tolerant_fallback is False

    runtime = create_data_perception_runtime(config)
    assert runtime is not None
    assert runtime.max_artifacts == 20
    assert runtime.max_report_chars == 9000
    assert runtime.enable_database_inspection is False
