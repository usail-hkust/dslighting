from dslighting.prompts.workflows.react import create_react_prompt


def test_create_react_prompt_uses_structured_dslighting_format() -> None:
    prompt = create_react_prompt(
        {
            "goal_and_data": "Predict house prices from tabular data.",
            "io_instructions": "--- CRITICAL I/O REQUIREMENTS ---\nWrite submission.csv in the working directory.",
        },
        output_filename="submission.csv",
    )

    assert prompt.startswith(
        "Role: You are an expert Data Scientist and AI Engineer operating in a strict ReAct workflow."
    )
    assert "Task Goal and Data Overview: Predict house prices from tabular data." in prompt
    assert "CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED): Write submission.csv in the working directory." in prompt
    assert "Instructions:" in prompt
    assert "Response Format: Your response MUST contain exactly <Think>...</Think> and then either <Action>...</Action> or <Answer>...</Answer>." in prompt
    assert "Never output <Final Answer> or any other completion tag variant." in prompt
    assert "Always close every tag explicitly. In particular, finish completion replies with </Answer>." in prompt
    assert "required artifact has already been created" not in prompt
    assert "exact filename `submission.csv`" not in prompt
    assert "Termination Rule: Stop writing code and return <Answer>...</Answer> only when no additional execution is needed." in prompt
