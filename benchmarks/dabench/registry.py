from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import logging
from appdirs import user_cache_dir

from mlebench.grade_helpers import Grader
from mlebench.utils import import_fn, load_yaml

logger = logging.getLogger(__name__)


DEFAULT_DATA_DIR = (Path(user_cache_dir()) / "mle-bench" / "data").resolve()


def _get_module_dir() -> Path:
    """Returns an absolute path to the dabench module."""
    path = Path(__file__).parent.resolve()
    assert path.name == "dabench", f"Expected module directory to be `dabench`, got `{path.name}`."
    return path


def _get_repo_dir() -> Path:
    """Returns repository root (parent of benchmarks directory)."""
    # module at benchmarks/dabench -> repo root is two levels up
    return _get_module_dir().parent.parent


@dataclass(frozen=True)
class Competition:
    id: str
    name: str
    description: str
    grader: Grader
    answers: Path
    gold_submission: Path
    sample_submission: Path
    competition_type: str
    prepare_fn: Callable[[Path, Path, Path], Path]
    raw_dir: Path
    private_dir: Path
    public_dir: Path
    checksums: Path
    leaderboard: Path

    def __post_init__(self):
        assert isinstance(self.id, str), "Competition id must be a string."
        assert isinstance(self.name, str), "Competition name must be a string."
        assert isinstance(self.description, str), "Competition description must be a string."
        assert isinstance(self.grader, Grader), "Competition grader must be of type Grader."
        assert isinstance(self.answers, Path), "Competition answers must be a Path."
        assert isinstance(self.gold_submission, Path), "Gold submission must be a Path."
        assert isinstance(self.sample_submission, Path), "Sample submission must be a Path."
        assert isinstance(self.competition_type, str), "Competition type must be a string."
        assert isinstance(self.checksums, Path), "Checksums must be a Path."
        assert isinstance(self.leaderboard, Path), "Leaderboard must be a Path."
        assert len(self.id) > 0, "Competition id cannot be empty."
        assert len(self.name) > 0, "Competition name cannot be empty."
        assert len(self.description) > 0, "Competition description cannot be empty."
        assert len(self.competition_type) > 0, "Competition type cannot be empty."

    @staticmethod
    def from_dict(data: dict) -> "Competition":
        grader = Grader.from_dict(data["grader"])

        try:
            return Competition(
                id=data["id"],
                name=data["name"],
                description=data["description"],
                grader=grader,
                answers=data["answers"],
                sample_submission=data["sample_submission"],
                gold_submission=data["gold_submission"],
                competition_type=data["competition_type"],
                prepare_fn=data["prepare_fn"],
                raw_dir=data["raw_dir"],
                public_dir=data["public_dir"],
                private_dir=data["private_dir"],
                checksums=data["checksums"],
                leaderboard=data["leaderboard"],
            )
        except KeyError as e:
            raise ValueError(f"Missing key {e} in competition config!")


class Registry:
    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR):
        self._data_dir = data_dir.resolve()
        self.mode = "test"

    def _resolve_competition_root(self, competition_id: str) -> Path:
        """
        Resolve where a competition config lives.
        Primary: dabench/competitions/.
        Fallback: mlebench/competitions/ for legacy references.
        """
        repo_dir = _get_repo_dir()
        dabench_root = repo_dir / "benchmarks" / "dabench" / "competitions"
        legacy_root = repo_dir / "benchmarks" / "mlebench" / "competitions"

        if (dabench_root / competition_id).exists():
            return dabench_root
        if (legacy_root / competition_id).exists():
            return legacy_root
        return dabench_root

    def set_mode(self, mode: str = "test"):
        """Set the mode of the registry."""
        assert mode in ["test", "validation", "prepare"], "Mode must be in ['test', 'validation', 'prepare']."
        self.mode = mode

    def get_competition(self, competition_id: str) -> Competition:
        """Fetch the competition from the registry."""

        root_dir = self._resolve_competition_root(competition_id)

        config_path = root_dir / competition_id / "config.yaml"
        config = load_yaml(config_path)

        checksums_path = root_dir / competition_id / "checksums.yaml"
        leaderboard_path = root_dir / competition_id / "leaderboard.csv"

        description_path = _get_repo_dir() / config["description"]
        if not description_path.exists() and config["description"].startswith("mlebench/"):
            description_path = _get_repo_dir() / "benchmarks" / config["description"]
        description = description_path.read_text()

        # Config for different modes
        config_preparer = config["preparer"]
        config_answers = config["dataset"]["answers"]
        config_sample_submission = config["dataset"]["sample_submission"]
        public_folder = "public"
        private_folder = "private"

        if self.mode == "prepare":
            config_preparer = config_preparer.replace("prepare:", "prepare_val:")

        elif self.mode == "validation":
            config_preparer = config_preparer.replace("prepare:", "prepare_val:")
            config_answers = config_answers.replace("/private/", "/private_val/")
            config_sample_submission = config_sample_submission.replace("/public/", "/public_val/")
            public_folder = "public_val"
            private_folder = "private_val"

        preparer_fn = import_fn(config_preparer)

        answers = self.get_data_dir() / config_answers
        gold_submission = answers
        if "gold_submission" in config["dataset"]:
            gold_submission = self.get_data_dir() / config["dataset"]["gold_submission"]
        sample_submission = self.get_data_dir() / config_sample_submission

        raw_dir = self.get_data_dir() / competition_id / "raw"
        private_dir = self.get_data_dir() / competition_id / "prepared" / private_folder
        public_dir = self.get_data_dir() / competition_id / "prepared" / public_folder

        return Competition.from_dict(
            {
                **config,
                "description": description,
                "answers": answers,
                "sample_submission": sample_submission,
                "gold_submission": gold_submission,
                "prepare_fn": preparer_fn,
                "raw_dir": raw_dir,
                "private_dir": private_dir,
                "public_dir": public_dir,
                "checksums": checksums_path,
                "leaderboard": leaderboard_path,
            }
        )

    def get_competitions_dir(self) -> Path:
        """Retrieves the competition directory within the registry."""
        return _get_module_dir() / "competitions"

    def get_splits_dir(self) -> Path:
        """Retrieves the splits directory within the repository."""
        return _get_repo_dir() / "experiments" / "splits"

    def get_data_dir(self) -> Path:
        """Retrieves the data directory within the registry."""
        return self._data_dir

    def set_data_dir(self, new_data_dir: Path) -> "Registry":
        """Sets the data directory within the registry."""
        return Registry(new_data_dir)

    def list_competition_ids(self) -> list[str]:
        """List all competition IDs available in the registry, sorted alphabetically."""

        repo_dir = _get_repo_dir()
        legacy_root = repo_dir / "mlebench" / "competitions"

        search_roots = [self.get_competitions_dir()]
        if legacy_root.exists():
            search_roots.append(legacy_root)

        competition_ids: set[str] = set()
        for root in search_roots:
            for cfg in root.rglob("config.yaml"):
                competition_ids.add(cfg.parent.stem)

        return sorted(competition_ids)


registry = Registry()
