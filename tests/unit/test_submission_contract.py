"""Tests for submission contract utilities: tag extraction and reminder building."""

from __future__ import annotations

from pathlib import Path

from dslighting.utils.submission_contract import (
    build_tag_contract_reminder,
    extract_submission_tag_contract,
    find_sample_submission_file,
)


def test_extract_submission_tag_contract_detects_required_tags(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    sample = data_dir / "sample_submission.csv"
    sample.write_text(
        "id,answer\n1,@city[nyc] @score[0.12]\n2,@city[sf] @score[0.89]\n",
        encoding="utf-8",
    )

    sample_submission = find_sample_submission_file(data_dir)
    contract = extract_submission_tag_contract(sample_submission)

    assert contract["tag_wrapper_required"] is True
    assert contract["required_tags"] == ["city", "score"]

    reminder = build_tag_contract_reminder(contract)
    assert "UNIFIED TAGGED SUBMISSION CONTRACT (MANDATORY):" in reminder
    assert "@tag[...]" in reminder


def test_extract_submission_tag_contract_placeholder_only_still_requires_wrapper(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    sample = data_dir / "sample_submission.csv"
    sample.write_text("id,answer\n1,@placeholder[0.00]\n", encoding="utf-8")

    contract = extract_submission_tag_contract(sample)

    assert contract["tag_wrapper_required"] is True
    assert contract["required_tags"] == []
    assert "placeholder" in contract["forbidden_tags"]
