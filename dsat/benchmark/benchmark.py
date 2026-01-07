import asyncio
import json
from pathlib import Path
from typing import Any, Callable, List, Tuple, Optional, Dict
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class BaseBenchmark:
    """
    Abstract base class for all benchmark tests.
    """
    def __init__(self, name: str, file_path: Optional[str], log_path: str, **kwargs):
        self.name = name
        self.file_path = file_path
        self.log_path = log_path
        self.problems = self._load_problems()
        # self.results_path = Path(self.log_path) / f"{self.name}_results.csv"
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_path = Path(self.log_path) / f"{self.name}_results_{timestamp}.csv"
        self.mismatches_path = Path(self.log_path) / f"{self.name}_mismatches.log"

    def _load_problems(self) -> List[Dict[str, Any]]:
        """Load problems from jsonl file."""
        # MODIFICATION: Handle cases where file_path is not provided.
        if not self.file_path:
            logger.debug("No file_path provided. Subclass is expected to override _load_problems.")
            return []
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def get_result_columns(self) -> List[str]:
        raise NotImplementedError

    async def evaluate_problem(self, problem: Dict, eval_fn: Callable, **kwargs) -> Tuple:
        raise NotImplementedError

    def log_mismatch(self, **kwargs):
        with open(self.mismatches_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(kwargs) + "\n")

    # REFACTORED: The main evaluation loop now accepts and passes down `eval_fn`.
    async def run_evaluation(self, eval_fn: Callable, **kwargs):
        """
        Run the entire benchmark evaluation.

        Args:
            eval_fn: The generic evaluation function provided by DSATRunner.get_eval_function().
        """
        if not self.problems:
            logger.error(f"Evaluation for '{self.name}' aborted: No problems were loaded.")
            return

        logger.info(f"Starting evaluation for benchmark '{self.name}' with {len(self.problems)} problems.")

        results = []
        tasks = [self.evaluate_problem(problem, eval_fn=eval_fn) for problem in self.problems]

        # Use native asyncio for task completion
        for future in asyncio.as_completed(tasks):
            try:
                # evaluate_problem returns (csv_tuple, report, error_message)
                result_tuple, report, error_message = await future
                results.append(result_tuple)
            except Exception as e:
                logger.error(f"An unexpected error occurred in evaluate_problem: {e}", exc_info=True)

        # Save results to CSV
        df = pd.DataFrame(results, columns=self.get_result_columns())
        df.to_csv(self.results_path, index=False)

        # Add metadata summary
        self._append_metadata_to_csv(df, **kwargs)

        logger.info(f"Evaluation complete. Results saved to {self.results_path}")

    def _append_metadata_to_csv(self, df: pd.DataFrame, **kwargs):
        """Append metadata summary to the CSV file."""
        try:
            import numpy as np

            # Calculate statistics
            score_col = 'score' if 'score' in df.columns else None
            cost_col = 'cost' if 'cost' in df.columns else None
            running_time_col = 'running_time' if 'running_time' in df.columns else None
            input_tokens_col = 'input_tokens' if 'input_tokens' in df.columns else None
            output_tokens_col = 'output_tokens' if 'output_tokens' in df.columns else None
            total_tokens_col = 'total_tokens' if 'total_tokens' in df.columns else None

            stats = {}
            if score_col:
                valid_scores = df[score_col].dropna()
                if len(valid_scores) > 0:
                    stats['avg_score'] = valid_scores.mean()
                    stats['median_score'] = valid_scores.median()
                    stats['std_score'] = valid_scores.std()

            if cost_col:
                valid_costs = df[cost_col].dropna()
                if len(valid_costs) > 0:
                    stats['avg_cost'] = valid_costs.mean()
                    stats['total_cost'] = valid_costs.sum()

            if running_time_col:
                valid_times = df[running_time_col].dropna()
                if len(valid_times) > 0:
                    stats['avg_running_time'] = valid_times.mean()
                    stats['total_running_time'] = valid_times.sum()

            if input_tokens_col:
                valid_input_tokens = df[input_tokens_col].dropna()
                if len(valid_input_tokens) > 0:
                    stats['avg_input_tokens'] = valid_input_tokens.mean()
                    stats['total_input_tokens'] = valid_input_tokens.sum()

            if output_tokens_col:
                valid_output_tokens = df[output_tokens_col].dropna()
                if len(valid_output_tokens) > 0:
                    stats['avg_output_tokens'] = valid_output_tokens.mean()
                    stats['total_output_tokens'] = valid_output_tokens.sum()

            if total_tokens_col:
                valid_total_tokens = df[total_tokens_col].dropna()
                if len(valid_total_tokens) > 0:
                    stats['avg_total_tokens'] = valid_total_tokens.mean()
                    stats['total_total_tokens'] = valid_total_tokens.sum()

            # Get model info from kwargs
            model_info = kwargs.get('model_name', 'N/A')

            # Create metadata rows
            meta_rows = [
                [''] * len(df.columns),  # Empty separator row
                ['=== METADATA ==='] + [''] * (len(df.columns) - 1),
            ]

            meta_data = {
                'Model': model_info,
                'Total Tasks': len(df),
                'Average Score': f"{stats.get('avg_score', 0):.4f}" if 'avg_score' in stats else 'N/A',
                'Median Score': f"{stats.get('median_score', 0):.4f}" if 'median_score' in stats else 'N/A',
                'Std Score': f"{stats.get('std_score', 0):.4f}" if 'std_score' in stats else 'N/A',
                'Average Cost': f"${stats.get('avg_cost', 0):.4f}" if 'avg_cost' in stats else 'N/A',
                'Total Cost': f"${stats.get('total_cost', 0):.4f}" if 'total_cost' in stats else 'N/A',
                'Average Running Time': f"{stats.get('avg_running_time', 0):.4f}s" if 'avg_running_time' in stats else 'N/A',
                'Total Running Time': f"{stats.get('total_running_time', 0):.4f}s" if 'total_running_time' in stats else 'N/A',
                'Average Input Tokens': f"{stats.get('avg_input_tokens', 0):.0f}" if 'avg_input_tokens' in stats else 'N/A',
                'Total Input Tokens': f"{stats.get('total_input_tokens', 0):.0f}" if 'total_input_tokens' in stats else 'N/A',
                'Average Output Tokens': f"{stats.get('avg_output_tokens', 0):.0f}" if 'avg_output_tokens' in stats else 'N/A',
                'Total Output Tokens': f"{stats.get('total_output_tokens', 0):.0f}" if 'total_output_tokens' in stats else 'N/A',
                'Average Total Tokens': f"{stats.get('avg_total_tokens', 0):.0f}" if 'avg_total_tokens' in stats else 'N/A',
                'Total Total Tokens': f"{stats.get('total_total_tokens', 0):.0f}" if 'total_total_tokens' in stats else 'N/A',
            }

            for key, value in meta_data.items():
                meta_rows.append([key, value] + [''] * (len(df.columns) - 2))

            # Append to CSV
            with open(self.results_path, 'a', encoding='utf-8') as f:
                for row in meta_rows:
                    f.write(','.join(str(x) for x in row) + '\n')

            logger.info(f"Metadata appended to {self.results_path}")
        except Exception as e:
            logger.warning(f"Failed to append metadata: {e}")