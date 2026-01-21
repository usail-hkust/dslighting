from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Callable

from appdirs import user_cache_dir

from dslighting.benchmark.mlebench.grade_helpers import Grader
from dslighting.benchmark.mlebench.utils import get_logger, get_module_dir, get_repo_dir, import_fn, load_yaml

logger = get_logger(__name__)


DEFAULT_DATA_DIR = (Path(user_cache_dir()) / "mle-bench" / "data").resolve()


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
        self.mode = 'test'

    def _coerce_file_import(
        self, fn_import_string: str, root_dir: Path, competition_id: str
    ) -> str:
        if fn_import_string.startswith("file:"):
            return fn_import_string

        module_name, fn_name = fn_import_string.split(":")
        try:
            importlib.import_module(module_name)
            return fn_import_string
        except ModuleNotFoundError as exc:
            if exc.name != module_name and not module_name.startswith(f"{exc.name}."):
                raise

            leaf = module_name.split(".")[-1]
            file_module = root_dir / competition_id / f"{leaf}.py"
            if not file_module.exists() and leaf.endswith("_val"):
                fallback = root_dir / competition_id / f"{leaf[:-4]}.py"
                if fallback.exists():
                    file_module = fallback

            if not file_module.exists():
                raise

            return f"file:{file_module}:{fn_name}"

    def _resolve_competition_root(self, competition_id: str) -> Path:
        """
        Resolve where a competition config lives.
        - Prefer top-level `dabench/` for DABench-prefixed tasks.
        - Check `data_dir` for user-uploaded tasks.
        - Fallback to legacy `mlebench/competitions/` for everything else.
        """
        # New layout: benchmarks/mlebench and benchmarks/dabench sit under repo root.
        repo_dir = get_repo_dir()
        dabench_root = repo_dir / "benchmarks" / "dabench" / "competitions"
        legacy_root = repo_dir / "benchmarks" / "mlebench" / "competitions"

        if competition_id.startswith("dabench-") and (dabench_root / competition_id).exists():
            return dabench_root
        
        # Check if the competition is in the data directory (user uploaded)
        if (self._data_dir / competition_id / "config.yaml").exists():
            return self._data_dir

        if (legacy_root / competition_id).exists():
            return legacy_root
        if (dabench_root / competition_id).exists():
            return dabench_root
        return legacy_root

    def set_mode(self, mode: str = 'test'):
        """Set the mode of the registry.
        Args:
            mode: The mode of the registry. Can be 'test' or 'validation'.
        """
        assert mode in ['test', 'validation', 'prepare'], "Mode must be in ['test', 'validation', 'prepare']."
        self.mode = mode

    def get_competition(self, competition_id: str) -> Competition:
        """Fetch the competition from the registry."""

        root_dir = self._resolve_competition_root(competition_id)
        is_dabench = root_dir.name == "competitions" and root_dir.parent.name == "dabench"

        config_path = root_dir / competition_id / "config.yaml"
        config = load_yaml(config_path)

        checksums_path = root_dir / competition_id / "checksums.yaml"
        leaderboard_path = root_dir / competition_id / "leaderboard.csv"

        # Resolve description file. DABench configs may still point to legacy paths.
        if root_dir.name == "competitions" and root_dir.parent.name == "dabench":
            description_path = root_dir / competition_id / "description.md"
        else:
            # Try to find description relative to competition dir first
            candidate_desc = root_dir / competition_id / config["description"]
            if candidate_desc.exists():
                description_path = candidate_desc
            else:
                description_path = get_repo_dir() / config["description"]
                if not description_path.exists() and config["description"].startswith("mlebench/"):
                    description_path = get_repo_dir() / "benchmarks" / config["description"]
        description = description_path.read_text()

        # Config for different modes
        base_preparer = config["preparer"]
        base_answers = config["dataset"]["answers"]
        base_sample_submission = config["dataset"]["sample_submission"]

        config_preparer = base_preparer
        config_answers = base_answers
        config_sample_submission = base_sample_submission
        public_folder = 'public'
        private_folder = 'private'

        if is_dabench:
            # DABench evaluation should NOT depend on any prepare logic; always use the
            # existing prepared/public + prepared/private folders.
            config_preparer = base_preparer
            config_answers = base_answers
            config_sample_submission = base_sample_submission
            public_folder = "public"
            private_folder = "private"
        else:
            if self.mode == 'prepare':
                config_preparer = config_preparer.replace('prepare:', 'prepare_val:')

            elif self.mode == 'validation':
                config_preparer = config_preparer.replace('prepare:', 'prepare_val:')
                config_answers = config_answers.replace('/private/', '/private_val/')
                config_sample_submission = config_sample_submission.replace('/public/', '/public_val/')
                public_folder = 'public_val'
                private_folder = 'private_val'

            # Some benchmarks may not provide *_val splits; if missing, fall back to test artifacts.
            if self.mode == "validation":
                data_dir = self.get_data_dir()
                answers_candidate = data_dir / config_answers
                sample_candidate = data_dir / config_sample_submission
                public_candidate = data_dir / competition_id / "prepared" / public_folder
                private_candidate = data_dir / competition_id / "prepared" / private_folder
                if not (
                    answers_candidate.exists()
                    and sample_candidate.exists()
                    and public_candidate.exists()
                    and private_candidate.exists()
                ):
                    config_preparer = base_preparer
                    config_answers = base_answers
                    config_sample_submission = base_sample_submission
                    public_folder = "public"
                    private_folder = "private"

        # DABench competitions are not importable as Python packages (hyphenated ids).
        # Convert legacy import strings to file-based imports under the resolved root_dir.
        if is_dabench:
            module_str, fn_name = config_preparer.split(":")
            leaf = module_str.split(".")[-1]  # prepare or grade
            file_module = root_dir / competition_id / f"{leaf}.py"
            if not file_module.exists() and leaf.endswith("_val"):
                fallback = root_dir / competition_id / f"{leaf[:-4]}.py"
                if fallback.exists():
                    file_module = fallback
            config_preparer = f"file:{file_module}:{fn_name}"
            if "grader" in config and "grade_fn" in config["grader"]:
                g_module_str, g_fn_name = config["grader"]["grade_fn"].split(":")
                g_leaf = g_module_str.split(".")[-1]
                g_file_module = root_dir / competition_id / f"{g_leaf}.py"
                if not g_file_module.exists() and g_leaf.endswith("_val"):
                    g_fallback = root_dir / competition_id / f"{g_leaf[:-4]}.py"
                    if g_fallback.exists():
                        g_file_module = g_fallback
                config["grader"]["grade_fn"] = f"file:{g_file_module}:{g_fn_name}"
        else:
            config_preparer = self._coerce_file_import(
                config_preparer, root_dir, competition_id
            )
            if "grader" in config and "grade_fn" in config["grader"]:
                config["grader"]["grade_fn"] = self._coerce_file_import(
                    config["grader"]["grade_fn"], root_dir, competition_id
                )

        if is_dabench:
            def preparer_fn(raw: Path, public: Path, private: Path) -> Path:
                logger.info(
                    "DABench prepare disabled; using existing prepared/public + prepared/private."
                )
                return public
        else:
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

        return get_module_dir() / "competitions"

    def get_splits_dir(self) -> Path:
        """Retrieves the splits directory within the repository."""

        return get_repo_dir() / "experiments" / "splits"

    def get_lite_competition_ids(self) -> list[str]:
        """List all competition IDs for the lite version (low complexity competitions)."""

        lite_competitions_file = self.get_splits_dir() / "low.txt"
        with open(lite_competitions_file, "r") as f:
            competition_ids = f.read().splitlines()
        return competition_ids

    def get_data_dir(self) -> Path:
        """Retrieves the data directory within the registry."""

        return self._data_dir

    def set_data_dir(self, new_data_dir: Path) -> "Registry":
        """Sets the data directory within the registry."""

        return Registry(new_data_dir)

    def list_competition_ids(self) -> list[str]:
        """List all competition IDs available in the registry, sorted alphabetically."""

        repo_dir = get_repo_dir()
        dabench_root = repo_dir / "dabench" / "competitions"

        search_roots = [repo_dir / "benchmarks" / "mlebench" / "competitions"]
        if dabench_root.exists():
            search_roots.append(dabench_root)

        competition_ids: set[str] = set()
        for root in search_roots:
            for cfg in root.rglob("config.yaml"):
                competition_ids.add(cfg.parent.stem)

        return sorted(competition_ids)


registry = Registry()
