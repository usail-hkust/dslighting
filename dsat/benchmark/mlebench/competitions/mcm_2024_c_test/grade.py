import os
from pathlib import Path
from typing import Any
import pandas as pd

# This is a generic LLM-based grader for open-ended tasks.
# It reads 'rubric.md' from the task directory and evaluates the submission.

try:
    from dsat.services.llm import LLMService
    from dsat.config import LLMConfig
except ImportError:
    # Fallback for when running outside of dsat package context
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    from dsat.services.llm import LLMService
    from dsat.config import LLMConfig

class Report:
    def __init__(self, score, feedback):
        self.score = score
        self.feedback = feedback
        # Standard fields expected by the framework
        self.is_lower_better = False
        self.submission_exists = True
        self.valid_submission = True
        self.gold_medal = score >= 0.9
        self.silver_medal = score >= 0.7
        self.bronze_medal = score >= 0.5
        self.above_median = score >= 0.5
        self.submission_path = ""
        self.competition_id = "open_ended_task"

def grade(submission_path: Path, competition: Any) -> Report:
    """
    Grades the submission using an LLM Judge against rubric.md.
    """
    # 1. Load the Rubric
    task_dir = competition.raw_dir.parent
    rubric_path = task_dir / "rubric.md"
    
    if not rubric_path.exists():
        # Fallback if no rubric exists
        print(f"Warning: Rubric not found at {rubric_path}. Returning default score.")
        return Report(0.5, "No grading rubric defined.")
        
    rubric_content = rubric_path.read_text(encoding="utf-8")
    
    # 2. Load the Submission Content (Preview)
    # Since it's open-ended, the 'submission_path' might be a CSV, code, or just a marker.
    # We'll try to peek at the output artifacts if possible, or assume the agent's recent work 
    # is what we are grading. Ideally, AIDE produces a submission file.
    
    submission_content = "No submission content readable."
    if submission_path.exists():
        try:
            if submission_path.suffix == '.csv':
                df = pd.read_csv(submission_path)
                submission_content = f"CSV Submission Preview:\n{df.head().to_markdown()}"
            else:
                submission_content = submission_path.read_text(encoding="utf-8")[:2000]
        except Exception as e:
            submission_content = f"Error reading submission: {e}"

    # 3. Setup LLM for Judging
    # Note: In a real run, we might want to inject the API key securely.
    # Here we assume environment variables are set (which they are in DSATRunner).
    try:
        api_key = os.getenv("API_KEY", "EMPTY")
        base_url = os.getenv("API_BASE", "https://api.openai.com/v1")
        model = os.getenv("LLM_MODEL", "gpt-4o")
        
        llm = LLMService(LLMConfig(api_key=api_key, api_base=base_url, model=model))
        
        prompt = f"""You are an impartial Judge. Evaluate the following submission against the provided Rubric.

# RUBRIC
{rubric_content}

# SUBMISSION CONTENT
{submission_content}

# INSTRUCTION
Assess the submission. 
Output ONLY a float number between 0.0 and 1.0 on the first line.
On subsequent lines, provide brief feedback.
"""
        # Synchronous call wrapper or direct call if possible. 
        # Since grade() is synchronous in standard mlebench, we need a way to run async code.
        import asyncio
        response = asyncio.run(llm.achat([{"role": "user", "content": prompt}]))
        
        lines = response.strip().split('\n')
        try:
            score = float(lines[0].strip())
        except ValueError:
            # Fallback if LLM is chatty
            import re
            match = re.search(r"(\d+(\.\d+)?)", lines[0])
            score = float(match.group(1)) if match else 0.5
            
        feedback = "\n".join(lines[1:])
        return Report(score, feedback)

    except Exception as e:
        print(f"LLM Judging failed: {e}")
        return Report(0.0, f"Judging failed: {e}")
