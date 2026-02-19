from __future__ import annotations


def test_error_module_has_no_deprecated_alias_exports() -> None:
    import dslighting.error as err

    forbidden_attrs = (
        "ErrorFormatter",
        "DSLightingFrameworkError",
        "InvalidConfigError",
        "WorkflowExecutionError",
        "BenchmarkTaskLoadError",
        "LLMError",
        "SandboxError",
        "TaskConfigInvalidError",
        "TaskRegistryNotFoundError",
        "CompetitionContextMissingError",
    )

    for name in forbidden_attrs:
        assert not hasattr(err, name), f"dslighting.error should not export {name}"


def test_public_namespaces_have_no_removed_aliases() -> None:
    import dslighting
    import dslighting.api as api
    import dslighting.datasets as datasets
    import dslighting.prompts as prompts

    assert not hasattr(dslighting, "ErrorFormatter")
    assert not hasattr(api, "get_default_paths")
    assert not hasattr(datasets, "load_dataset")
    assert not hasattr(prompts, "create_debug_prompt")
