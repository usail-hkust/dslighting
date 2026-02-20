from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from dslighting.cli.__main__ import build_cli_parser, cmd_detect_packages


def test_build_cli_parser_supports_completion_flags() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--completions", "bash"])
    assert args.completions == "bash"

    args = parser.parse_args(["--show-completion"])
    assert args.show_completion == "bash"


def test_detect_packages_flags_are_mutually_exclusive() -> None:
    parser = build_cli_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["detect-packages", "--all", "--data-science-only"])


def test_cmd_detect_packages_passes_data_science_only_true(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    class _FakeDetector:
        def detect_packages(self):
            return {"numpy": "1.0", "requests": "2.0"}

        def get_data_science_packages(self):
            return {"numpy": "1.0"}

        def save_to_config(self, config_path, packages, data_science_only):
            captured["config_path"] = config_path
            captured["packages"] = packages
            captured["data_science_only"] = data_science_only

    monkeypatch.setattr("dslighting.utils.package_detector.PackageDetector", _FakeDetector)

    args = argparse.Namespace(config=str(tmp_path / "config.yaml"), all=False, data_science_only=True)
    cmd_detect_packages(args)

    assert captured["data_science_only"] is True


def test_cmd_detect_packages_passes_data_science_only_false(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    class _FakeDetector:
        def detect_packages(self):
            return {"numpy": "1.0", "requests": "2.0"}

        def get_data_science_packages(self):
            return {"numpy": "1.0"}

        def save_to_config(self, config_path, packages, data_science_only):
            captured["config_path"] = config_path
            captured["packages"] = packages
            captured["data_science_only"] = data_science_only

    monkeypatch.setattr("dslighting.utils.package_detector.PackageDetector", _FakeDetector)

    args = argparse.Namespace(config=str(tmp_path / "config.yaml"), all=True, data_science_only=False)
    cmd_detect_packages(args)

    assert captured["data_science_only"] is False
