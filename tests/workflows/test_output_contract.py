from __future__ import annotations

from pathlib import Path

from dslighting.workflows.output_contract import (
    inspect_output_contract,
    render_output_contract_status,
    resolve_runner_output_candidate,
)


def test_output_contract_finds_exact_expected_file(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    expected = sandbox / "submission_task_abcd.csv"
    expected.write_text("prediction\n1\n", encoding="utf-8")

    status = inspect_output_contract(
        sandbox_workdir=sandbox,
        output_path=tmp_path / "out" / expected.name,
    )

    assert status.exists is True
    assert status.accepted_path == expected
    assert status.accepted_via_fallback is False
    rendered = render_output_contract_status(status)
    assert '<SubmissionStatus critical="true">' in rendered
    assert "exists: true" in rendered


def test_output_contract_uses_runner_hash_suffix_fallback(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    fallback = sandbox / "submission_task_livehash.csv"
    fallback.write_text("prediction\n1\n", encoding="utf-8")
    output_path = tmp_path / "out" / "submission_task_expectedhash.csv"

    accepted, accepted_via_fallback = resolve_runner_output_candidate(
        sandbox_workdir=sandbox,
        output_path=output_path,
    )
    status = inspect_output_contract(
        sandbox_workdir=sandbox,
        output_path=output_path,
    )

    assert accepted == fallback
    assert accepted_via_fallback is True
    assert status.exists is True
    assert status.accepted_path == fallback
    assert status.accepted_via_fallback is True
