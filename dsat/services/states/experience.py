"""
Implements Experience, which manages the state of a meta-optimization process.
This is the core state representation for Paradigm 3 (AFlow-style) evolutionary search.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any, Dict, Tuple

import numpy as np

from dsat.models.candidates import WorkflowCandidate
from dsat.services.states.base import State
from dsat.services.workspace import WorkspaceService

logger = logging.getLogger(__name__)

class Experience(State):
    """
    Acts as the database for the meta-optimizer. It saves and loads
    workflow scores and modification history to guide the search process,
    persisting state to the filesystem within the run's workspace.
    """
    def __init__(self, workspace: WorkspaceService):
        self.workspace = workspace
        # Define paths within the managed workspace
        self.scores_file = workspace.get_path("state") / "scores.jsonl"
        self.experience_file = workspace.get_path("state") / "experience.json"
        self.candidates_dir = workspace.get_path("candidates")
        
        # Initialize state files if they don't exist
        self.scores_file.touch()
        if not self.experience_file.exists():
            with open(self.experience_file, 'w') as f:
                json.dump({}, f)

    def _load_all_candidates(self) -> List[WorkflowCandidate]:
        """Loads all recorded candidates from the scores file."""
        candidates = []
        if not self.scores_file.exists() or self.scores_file.stat().st_size == 0:
            return []
            
        with open(self.scores_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    score_type = data.get("score_type", "fitness")
                    if score_type not in {"fitness", "fine"}:
                        continue
                    code_path = Path(data['code_path'])
                    if code_path.exists():
                        with open(code_path, "r", encoding="utf-8") as code_file:
                            code = code_file.read()
                        candidates.append(
                            WorkflowCandidate(
                                workflow_code=code, 
                                fitness=data['fitness'],
                                round_num=data.get('round')
                            )
                        )
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Skipping malformed line in scores.jsonl: {e}")
        return candidates

    def get_experience_summary(self, parent_round_num: Optional[int]) -> str:
        """
        Loads and formats the experience log for a specific parent candidate.
        """
        if parent_round_num is None:
            parent_round_num = -1

        if not self.experience_file.exists():
            return "Experience log not found."

        with open(self.experience_file, "r", encoding="utf-8") as f:
            try:
                all_experience = json.load(f)
            except json.JSONDecodeError:
                return "Could not parse experience log."

        if not isinstance(all_experience, dict):
            return "Could not parse experience log."

        def _coerce_list(value: Any) -> list[dict]:
            if not isinstance(value, list):
                return []
            out: list[dict] = []
            for item in value:
                if isinstance(item, dict):
                    out.append(item)
            return out

        summary_lines = []
        if parent_round_num >= 0:
            summary_lines.append(f"History of modifications for parent from round {parent_round_num}:")
        else:
            summary_lines.append("History of modifications (no specific parent selected):")

        parent_key = str(parent_round_num)
        parent_exp = all_experience.get(parent_key) if isinstance(all_experience.get(parent_key), dict) else {}
        parent_success = _coerce_list(parent_exp.get("success"))
        parent_failure = _coerce_list(parent_exp.get("failure"))

        summary_lines.append("\n### Successful Modifications:")
        if parent_success:
            for mod in parent_success:
                child = mod.get("child_round")
                score_after = float(mod.get("score_after", 0.0) or 0.0)
                delta = mod.get("delta")
                delta_str = ""
                if isinstance(delta, (int, float)):
                    delta_str = f", Δ={float(delta):+.4f}"
                summary_lines.append(
                    f"- (Child Round {child}, New Score: {score_after:.4f}{delta_str}) {mod.get('modification','')}"
                )
        else:
            summary_lines.append("- (none yet)")

        summary_lines.append("\n### Failed Modifications:")
        if parent_failure:
            for mod in parent_failure:
                child = mod.get("child_round")
                score_after = float(mod.get("score_after", 0.0) or 0.0)
                delta = mod.get("delta")
                delta_str = ""
                if isinstance(delta, (int, float)):
                    delta_str = f", Δ={float(delta):+.4f}"
                summary_lines.append(
                    f"- (Child Round {child}, New Score: {score_after:.4f}{delta_str}) {mod.get('modification','')}"
                )
        else:
            summary_lines.append("- (none yet)")

        # Add global successful examples to give the optimizer concrete positive patterns,
        # even when the selected parent has no successes yet.
        global_success: list[Tuple[float, str, dict]] = []
        for pkey, pexp in all_experience.items():
            if not isinstance(pexp, dict):
                continue
            for mod in _coerce_list(pexp.get("success")):
                try:
                    score_after = float(mod.get("score_after", 0.0) or 0.0)
                except Exception:
                    score_after = 0.0
                global_success.append((score_after, str(pkey), mod))

        global_success.sort(key=lambda t: t[0], reverse=True)
        top_global = global_success[:5]
        summary_lines.append("\n### Successful Examples (Global Top-5):")
        if top_global:
            for score_after, pkey, mod in top_global:
                child = mod.get("child_round")
                delta = mod.get("delta")
                delta_str = ""
                if isinstance(delta, (int, float)):
                    delta_str = f", Δ={float(delta):+.4f}"
                summary_lines.append(
                    f"- (Parent {pkey} → Child {child}, Score: {score_after:.4f}{delta_str}) {mod.get('modification','')}"
                )
        else:
            summary_lines.append("- (none yet)")
        
        return "\n".join(summary_lines)

    def select_parent_candidate(self, top_k: int) -> Optional[WorkflowCandidate]:
        """
        Selects a parent candidate using a softmax probability distribution over the
        top_k best-performing unique candidates, balancing exploration and exploitation.
        """
        all_candidates = self._load_all_candidates()
        if not all_candidates:
            return None

        # Sort by fitness (higher is better) and take the top k
        sorted_candidates = sorted(all_candidates, key=lambda c: c.fitness or -1.0, reverse=True)
        top_candidates = sorted_candidates[:top_k]

        if not top_candidates:
            return None
        
        fitness_scores = np.array([c.fitness for c in top_candidates])
        # Softmax probabilities: e^score / sum(e^scores)
        probabilities = np.exp(fitness_scores) / np.sum(np.exp(fitness_scores))

        return np.random.choice(top_candidates, p=probabilities)

    def record_score(
        self,
        round_num: int,
        fitness: float,
        code: str,
        *,
        score_type: str = "fitness",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Saves the workflow code and appends its score to the log."""
        candidate_code_path = self.candidates_dir / f"round_{round_num}_workflow.py"
        with open(candidate_code_path, "w", encoding="utf-8") as f:
            f.write(code)

        with open(self.scores_file, "a", encoding="utf-8") as f:
            payload: Dict[str, Any] = {
                "round": round_num,
                "fitness": fitness,
                "code_path": str(candidate_code_path),
                "score_type": str(score_type or "fitness"),
            }
            if extra:
                payload["extra"] = extra
            f.write(json.dumps(payload) + "\n")

    def record_experience(self, parent_round: int, child_round: int, modification: str, score_before: float, score_after: float):
        """Records the outcome of a modification attempt in the experience log."""
        with open(self.experience_file, 'r+') as f:
            data = json.load(f)
            parent_key = str(parent_round)
            if parent_key not in data:
                data[parent_key] = {"success": [], "failure": []}
            
            outcome = {
                "child_round": child_round,
                "modification": modification,
                "score_before": float(score_before),
                "score_after": score_after,
                "delta": float(score_after) - float(score_before),
                "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            
            if score_after > score_before:
                data[parent_key]["success"].append(outcome)
            else:
                data[parent_key]["failure"].append(outcome)
            
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
