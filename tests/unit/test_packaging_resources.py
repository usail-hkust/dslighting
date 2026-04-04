from pathlib import Path

import dslighting


def test_vendor_competition_config_is_packaged():
    package_root = Path(dslighting.__file__).parent
    config_path = (
        package_root
        / "benchmark"
        / "vendor"
        / "mlebench"
        / "competitions"
        / "bike-sharing-demand"
        / "config.yaml"
    )
    assert config_path.is_file()


def test_vendor_competition_grade_script_is_packaged():
    package_root = Path(dslighting.__file__).parent
    grade_path = (
        package_root
        / "benchmark"
        / "vendor"
        / "mlebench"
        / "competitions"
        / "bike-sharing-demand"
        / "grade.py"
    )
    assert grade_path.is_file()
