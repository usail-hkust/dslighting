# dsat/benchmark/datasci.py

import json
import uuid
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List, Tuple, Optional, Dict
import pandas as pd
import logging

from dsat.benchmark.benchmark import BaseBenchmark
from dsat.models.task import TaskDefinition

logger = logging.getLogger(__name__)


class DataSciBenchmark(BaseBenchmark):
    """
    Benchmark class for DataSciBench tasks.
    
    DataSciBench tasks involve multi-step data science workflows where:
    - Input: prompt.json (task description) + optional input data files
    - Output: Generated files that are compared against ground truth
    - Evaluation: Uses metric.yaml to define evaluation functions
    """
    
    def __init__(
        self,
        name: str,
        file_path: Optional[str],
        log_path: str,
        datasci_root_dir: Optional[str] = None,
        tasks: Optional[List[str]] = None,
        **kwargs
    ):
        # Set up root directory before calling parent constructor
        if datasci_root_dir:
            self.root_dir = Path(datasci_root_dir)
        else:
            # Default to DataSciBench_Selected in benchmarks directory
            self.root_dir = Path(__file__).parent.parent.parent / "benchmarks" / "DataSciBench_Selected"
        
        self.data_dir = self.root_dir / "data"
        self.metric_dir = self.root_dir / "metric"
        self.gt_data_dir = self.root_dir / "gt_data"
        
        # Override tasks if provided via CLI
        self.task_filter = tasks
        
        # Call parent constructor (which calls _load_problems)
        super().__init__(name, file_path, log_path, **kwargs)
        
        Path(self.log_path).mkdir(parents=True, exist_ok=True)
        
        # Re-initialize problems after setting up directories
        self.problems = self._load_problems()
        logger.info(f"DataSciBenchmark initialized with root_dir: {self.root_dir}")
        logger.info(f"Loaded {len(self.problems)} tasks")
    
    def _load_problems(self) -> List[Dict[str, Any]]:
        """Load DataSciBench tasks from the data directory."""
        if not self.data_dir.exists():
            logger.error(f"DataSciBench data directory not found: {self.data_dir}")
            return []
        
        problems = []
        
        # Get all task directories
        task_dirs = sorted([d for d in self.data_dir.iterdir() if d.is_dir()])
        
        for task_dir in task_dirs:
            task_id = task_dir.name
            
            # Apply task filter if specified
            if self.task_filter and task_id not in self.task_filter:
                continue
            
            prompt_file = task_dir / "prompt.json"
            if not prompt_file.exists():
                logger.warning(f"Skipping task '{task_id}': no prompt.json found")
                continue
            
            # Load prompt
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
            except Exception as e:
                logger.warning(f"Skipping task '{task_id}': failed to load prompt.json: {e}")
                continue
            
            # Check for metric file
            metric_file = self.metric_dir / task_id / "metric.yaml"
            if not metric_file.exists():
                logger.warning(f"Skipping task '{task_id}': no metric.yaml found")
                continue
            
            # Get input files (exclude prompt.json)
            input_files = [f.name for f in task_dir.iterdir() 
                          if f.is_file() and f.name not in ('prompt.json', 'orig_prompt.json')]
            
            problems.append({
                "task_id": task_id,
                "prompt": prompt_data.get("prompt", ""),
                "data_source_type": prompt_data.get("data_source_type", "unknown"),
                "input_files": input_files,
                "task_dir": str(task_dir),
                "metric_file": str(metric_file),
                "gt_dir": str(self.gt_data_dir / task_id / "gt"),
            })
            logger.debug(f"Loaded task: {task_id}")
        
        if not problems:
            logger.error(f"No valid tasks found in {self.data_dir}")
        
        return problems
    
    def get_result_columns(self) -> List[str]:
        """Define columns for results CSV."""
        return [
            "task_id",
            "output_dir",
            "gt_dir", 
            "score",
            "cost",
            "files_generated",
            "evaluation_passed",
            "error_message",
        ]
    
    def _evaluate_task_outputs(
        self,
        task_id: str,
        output_dir: Path,
        metric_file: Path,
        gt_dir: Path
    ) -> Tuple[float, bool, Optional[str]]:
        """
        Evaluate task outputs using metric.yaml evaluation functions.
        
        Returns:
            Tuple of (score, passed, error_message)
        """
        try:
            # Load metric configuration
            with open(metric_file, 'r', encoding='utf-8') as f:
                metric_config = yaml.safe_load(f)
            
            if not metric_config or 'TMC-list' not in metric_config:
                return 0.0, False, "Invalid metric.yaml: missing TMC-list"
            
            tmc_list = metric_config['TMC-list']
            total_score = 0
            max_score = len(tmc_list) * 2  # Each task can score 0, 1, or 2
            
            for metric_item in tmc_list:
                eval_code = metric_item.get('code', '')
                gt_file = metric_item.get('ground_truth', '')
                
                if not eval_code:
                    continue
                
                # Prepare ground truth path
                gt_path = gt_dir / gt_file if gt_file else gt_dir
                
                try:
                    # Create evaluation context
                    import os
                    original_cwd = os.getcwd()
                    os.chdir(str(output_dir))
                    
                    # Execute evaluation code
                    local_vars = {'ground_truth': str(gt_path)}
                    exec(eval_code, {'__builtins__': __builtins__, 'pd': pd}, local_vars)
                    
                    # Find the evaluation function and call it
                    for name, obj in local_vars.items():
                        if callable(obj) and name != '__builtins__':
                            try:
                                result = obj(str(gt_path))
                                if result is True:
                                    total_score += 2
                                elif result is not None:
                                    total_score += 1
                            except Exception as func_error:
                                logger.debug(f"Evaluation function {name} failed: {func_error}")
                            break
                    
                    os.chdir(original_cwd)
                    
                except Exception as eval_error:
                    logger.debug(f"Evaluation error for {task_id}: {eval_error}")
                    try:
                        os.chdir(original_cwd)
                    except:
                        pass
            
            # Calculate normalized score (0-1)
            score = total_score / max_score if max_score > 0 else 0.0
            passed = score > 0
            
            return score, passed, None
            
        except Exception as e:
            return 0.0, False, str(e)
    
    async def evaluate_problem(
        self,
        problem: Dict[str, Any],
        eval_fn: Callable
    ) -> Tuple[Tuple, Any, Optional[str]]:
        """
        Evaluate a single DataSciBench task.
        """
        task_id = problem.get("task_id")
        if not task_id:
            raise ValueError("Problem data must contain 'task_id'")
        
        prompt = problem.get("prompt", "")
        task_dir = Path(problem.get("task_dir", ""))
        metric_file = Path(problem.get("metric_file", ""))
        gt_dir = Path(problem.get("gt_dir", ""))
        
        # Create unique output directory
        unique_id = uuid.uuid4().hex[:6]
        output_dir = Path(self.log_path) / f"output_{task_id}_{unique_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cost = 0.0
        error_message: Optional[str] = None
        files_generated = 0
        evaluation_passed = False
        score = 0.0
        
        try:
            # Create TaskDefinition for the workflow
            task = TaskDefinition(
                task_id=task_id,
                task_type="datasci",
                payload={
                    "prompt": prompt,
                    "input_dir": str(task_dir),
                    "output_dir": str(output_dir),
                    "expected_outputs": [],  # DataSciBench doesn't require specific output files
                }
            )
            
            # Execute the workflow
            result, cost = await eval_fn(task)
            
            # Check for errors
            if isinstance(result, str) and result.startswith("[ERROR]"):
                error_message = result
                logger.error(f"Task {task_id} failed: {error_message}")
            else:
                # Count generated files
                files_generated = len(list(output_dir.glob("*")))
                
                # Evaluate outputs against ground truth
                if metric_file.exists() and gt_dir.exists():
                    score, evaluation_passed, eval_error = self._evaluate_task_outputs(
                        task_id, output_dir, metric_file, gt_dir
                    )
                    if eval_error:
                        error_message = f"Evaluation error: {eval_error}"
                else:
                    # If no metric/gt, consider it passed if files were generated
                    evaluation_passed = files_generated > 0
                    score = 1.0 if evaluation_passed else 0.0
                
                logger.info(f"Task {task_id}: score={score:.2f}, files={files_generated}, passed={evaluation_passed}")
        
        except Exception as e:
            error_message = f"Error during DataSciBenchmark evaluation of {task_id}: {e}"
            logger.error(error_message, exc_info=True)
        
        # Build result tuple
        csv_tuple = (
            task_id,
            str(output_dir),
            str(gt_dir),
            score,
            cost,
            files_generated,
            evaluation_passed,
            error_message,
        )
        
        return csv_tuple, {"score": score, "passed": evaluation_passed}, error_message

