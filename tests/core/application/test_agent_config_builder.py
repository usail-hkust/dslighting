from dslighting.core.application.agent_config_builder import AgentConfigBuilder


def _make_builder(workflow_name: str, init_kwargs: dict):
    return AgentConfigBuilder(
        workflow_name=workflow_name,
        model="gpt-4o",
        api_key=None,
        api_base=None,
        provider=None,
        temperature=None,
        timeout=300,
        keep_workspace=True,
        init_kwargs=init_kwargs,
    )


def test_non_autokaggle_enforce_no_plotting_goes_to_search() -> None:
    builder = _make_builder("aide", {"max_iterations": 2})
    config = builder.build(task_id="task1", run_kwargs={"enforce_no_plotting": False})

    assert config.agent.search.max_iterations == 2
    assert config.agent.search.enforce_no_plotting is False


def test_autokaggle_enforce_no_plotting_goes_to_autokaggle() -> None:
    builder = _make_builder("autokaggle", {})
    config = builder.build(task_id="task1", run_kwargs={"enforce_no_plotting": False})

    assert config.agent.autokaggle.enforce_no_plotting is False


def test_runtime_kwargs_override_init_kwargs_and_unconsumed_go_to_parameters() -> None:
    builder = _make_builder("aide", {"max_iterations": 2, "custom_a": 1})
    config = builder.build(task_id="task1", run_kwargs={"max_iterations": 5, "custom_b": 2})

    assert config.agent.search.max_iterations == 5
    assert config.run.parameters["custom_a"] == 1
    assert config.run.parameters["custom_b"] == 2
