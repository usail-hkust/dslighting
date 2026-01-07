from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from benchmarks.sciencebench.grade_helpers import Grader
from benchmarks.sciencebench.utils import get_logger, get_module_dir, get_repo_dir, import_fn, load_yaml

logger = get_logger(__name__)


MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = (MODULE_DIR / "competitions").resolve()


@dataclass(frozen=True)
class Competition:
    id: str
    name: str
    description: str
    grader: Grader
    answers: Path
    gold_submission: Path
    sample_submission: Path
    submission_filename: Optional[str]
    competition_type: str
    prepare_fn: Callable[[Path, Path, Path], Path]
    raw_dir: Path
    private_dir: Path
    public_dir: Path
    leaderboard: Path

    def __post_init__(self):
        assert isinstance(self.id, str), "Competition id must be a string."
        assert isinstance(self.name, str), "Competition name must be a string."
        assert isinstance(self.description, str), "Competition description must be a string."
        assert isinstance(self.grader, Grader), "Competition grader must be of type Grader."
        assert isinstance(self.answers, Path), "Competition answers must be a Path."
        assert isinstance(self.gold_submission, Path), "Gold submission must be a Path."
        assert isinstance(self.sample_submission, Path), "Sample submission must be a Path."
        assert self.submission_filename is None or isinstance(
            self.submission_filename, str
        ), "submission_filename must be a string or None."
        assert isinstance(self.competition_type, str), "Competition type must be a string."
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
                submission_filename=data.get("submission_filename"),
                competition_type=data["competition_type"],
                prepare_fn=data["prepare_fn"],
                raw_dir=data["raw_dir"],
                public_dir=data["public_dir"],
                private_dir=data["private_dir"],
                leaderboard=data["leaderboard"],
            )
        except KeyError as e:
            raise ValueError(f"Missing key {e} in competition config!")


class Registry:
    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR):
        self._data_dir = data_dir.resolve()
        self.mode = 'test'

    def set_mode(self, mode: str = 'test'):
        """Set the mode of the registry.
        Args:
            mode: The mode of the registry. Can be 'test' or 'validation'.
        """
        assert mode in ['test', 'validation', 'prepare'], "Mode must be in ['test', 'validation', 'prepare']."
        self.mode = mode

    def get_competition(self, competition_id: str) -> Competition:
        """Fetch the competition from the registry."""

        config_path = self.get_competitions_dir() / competition_id / "config.yaml"
        config = load_yaml(config_path)

        leaderboard_path = self.get_competitions_dir() / competition_id / "leaderboard.csv"
        if not leaderboard_path.exists():
            # Create a placeholder leaderboard if it doesn't exist
            leaderboard_path.parent.mkdir(parents=True, exist_ok=True)
            leaderboard_path.write_text("competition_id,score\n")

        description_path = get_repo_dir() / config["description"]
        description = description_path.read_text()

        # Config for different modes
        config_preparer = config["preparer"]
        config_answers = config["dataset"]["answers"]
        config_sample_submission = config["dataset"]["sample_submission"]
        submission_filename = config.get("dataset", {}).get("submission_filename")
        public_folder = 'public'
        private_folder = 'private'

        if self.mode == 'prepare':
            config_preparer = config_preparer.replace('prepare:', 'prepare_val:')

        elif self.mode == 'validation':
            config_preparer = config_preparer.replace('prepare:', 'prepare_val:')
            config_answers = config_answers.replace('/private/', '/private_val/')
            config_sample_submission = config_sample_submission.replace('/public/', '/public_val/')
            public_folder = 'public_val'
            private_folder = 'private_val'

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
                "submission_filename": submission_filename,
                "prepare_fn": preparer_fn,
                "raw_dir": raw_dir,
                "private_dir": private_dir,
                "public_dir": public_dir,
                "leaderboard": leaderboard_path,
            }
        )

    def get_competitions_dir(self) -> Path:
        """Retrieves the competition directory within the registry."""
        return get_module_dir() / "competitions"

    def get_data_dir(self) -> Path:
        """Retrieves the data directory within the registry."""
        return self._data_dir

    def set_data_dir(self, new_data_dir: Path) -> "Registry":
        """Sets the data directory within the registry."""
        return Registry(new_data_dir)

    def list_competition_ids(self) -> list[str]:
        """List all competition IDs available in the registry, sorted alphabetically."""
        competition_configs = self.get_competitions_dir().rglob("config.yaml")
        competition_ids = [f.parent.stem for f in sorted(competition_configs)]
        return competition_ids


registry = Registry()
