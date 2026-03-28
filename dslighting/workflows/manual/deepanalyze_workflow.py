import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from dslighting.benchmark.core.base import BaseBenchmark
from dslighting.core.visualization_policy import (
    build_visualization_instruction_text,
    resolve_visualization_policy_from_agent_config,
)
from dslighting.services.llm import LLMService
from dslighting.services.sandbox import SandboxService
from dslighting.services.workspace import WorkspaceService
from dslighting.state.context import MAX_HISTORY_CHARS, MAX_OUTPUT_CHARS, truncate_output
from dslighting.workflows.base import BaseWorkflow
from dslighting.workflows.utils import (
    collect_output_files,
    extract_output_filenames_from_description,
    find_new_output_files,
    get_initial_sandbox_files,
)

logger = logging.getLogger(__name__)


class DeepAnalyzeWorkflow(BaseWorkflow):
    """
    Workflow implementation for DeepAnalyze-8B.

    DeepAnalyze uses structured tags (<Analyze>, <Code>, <Execute>, <Answer>) and requires
    multi-round dialog where the system injects code execution results into <Execute> tags.
    """

    def __init__(
        self,
        operators: Dict[str, Any],
        services: Dict[str, Any],
        agent_config: Dict[str, Any],
        benchmark: Optional[BaseBenchmark] = None,
    ):
        super().__init__(operators, services, agent_config)
        self.llm_service: LLMService = services["llm"]
        self.sandbox_service: SandboxService = services["sandbox"]
        self.workspace_service: WorkspaceService = services.get("workspace")
        self.execute_op = operators.get("execute")
        if not self.execute_op:
            raise ValueError("DeepAnalyzeWorkflow requires an 'execute' operator.")

        self.max_iterations = agent_config.get("max_iterations", 10)
        self.benchmark = benchmark
        self.visualization_policy = resolve_visualization_policy_from_agent_config(agent_config)

    @staticmethod
    def _extract_code_from_segment(segment: str) -> Optional[str]:
        """Extract python code between <Code>...</Code>, optionally fenced by ```python ... ```."""
        code_match = re.search(r"<Code>(.*?)</Code>", segment, re.DOTALL)
        if not code_match:
            return None
        code_content = code_match.group(1).strip()
        md_match = re.search(r"```(?:python)?(.*?)```", code_content, re.DOTALL)
        return (md_match.group(1).strip() if md_match else code_content)

    @staticmethod
    def _extract_answer_from_segment(segment: str) -> Optional[str]:
        """Extract answer content between <Answer>...</Answer> tags."""
        # Try case-insensitive match for <Answer> or <answer>
        answer_match = re.search(r"<Answer>(.*?)</Answer>", segment, re.DOTALL | re.IGNORECASE)
        if not answer_match:
            return None
        answer_content = answer_match.group(1).strip()
        # Remove "Answer:" prefix if present
        if "Answer:" in answer_content:
            answer_content = answer_content.split("Answer:", 1)[-1].strip()
        return answer_content

    def _should_terminate(self, response: str, iteration: int) -> bool:
        """Stop when an <Answer> block appears or max iterations reached."""
        # Some models emit a full <Answer>...</Answer> in one turn; others may emit
        # a bare </Answer> later. Prefer terminating as soon as any Answer block
        # is detected to avoid an extra empty turn.
        if re.search(r"<Answer>.*?</Answer>", response, re.DOTALL | re.IGNORECASE) or "</Answer>" in response:
            logger.info("Detected <Answer> block, stopping iterations.")
            return True
        if iteration + 1 >= self.max_iterations:
            logger.info("Reached maximum iterations, stopping workflow.")
            return True
        return False

    def _build_llm_messages(self, conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not conversation_history:
            return []

        max_chars = MAX_HISTORY_CHARS
        first = conversation_history[0]
        first_content = truncate_output(first.get("content", ""), max_chars // 2)
        messages = [{"role": first.get("role", "user"), "content": first_content}]
        total_chars = len(first_content)

        recent_messages = []
        for msg in reversed(conversation_history[1:]):
            content = truncate_output(msg.get("content", ""), MAX_OUTPUT_CHARS)
            msg_len = len(content)
            if total_chars + msg_len > max_chars:
                break
            recent_messages.append({"role": msg.get("role", "user"), "content": content})
            total_chars += msg_len

        messages.extend(reversed(recent_messages))
        return messages

    @staticmethod
    def _extract_output_filenames_from_description(description: str) -> List[str]:
        """Extract all potential output filenames from task description."""
        return extract_output_filenames_from_description(description)

    def _get_initial_sandbox_files(self, sandbox_workdir: Path) -> Set[str]:
        """Get the set of files initially present in sandbox (to detect new files later)."""
        return get_initial_sandbox_files(sandbox_workdir)

    def _find_new_output_files(self, sandbox_workdir: Path, initial_files: Set[str]) -> List[Path]:
        """Find all new files created in sandbox since initial state."""
        return find_new_output_files(sandbox_workdir, initial_files)

    def _collect_outputs_to_destination(
        self,
        sandbox_workdir: Path,
        output_path: Path,
        expected_filenames: List[str],
        initial_files: Set[str],
    ) -> bool:
        """Collect output files from sandbox to destination directory."""
        return collect_output_files(
            sandbox_workdir=sandbox_workdir,
            output_path=output_path,
            expected_filenames=expected_filenames,
            initial_files=initial_files,
        )

    def _write_answer_to_file(self, output_path: Path, answer_content: str) -> None:
        """Write answer content to output file based on file extension."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        suffix = output_path.suffix.lower()
        
        if suffix == '.txt':
            output_path.write_text(answer_content, encoding='utf-8')
            logger.info("Answer written to text file: %s", output_path)
            
        elif suffix == '.csv':
            # For CSV files, check if content looks like CSV data
            if '\n' in answer_content and ',' in answer_content:
                output_path.write_text(answer_content, encoding='utf-8')
            else:
                # Wrap simple answer in CSV format
                output_path.write_text(f"answer\n{answer_content}\n", encoding='utf-8')
            logger.info("Answer written to CSV file: %s", output_path)
            
        elif suffix == '.json':
            # Try to format as JSON if possible
            import json
            try:
                # Check if it's already valid JSON
                json.loads(answer_content)
                output_path.write_text(answer_content, encoding='utf-8')
            except json.JSONDecodeError:
                # Wrap in JSON format
                output_path.write_text(json.dumps({"answer": answer_content}), encoding='utf-8')
            logger.info("Answer written to JSON file: %s", output_path)
            
        else:
            # Default: write as plain text
            output_path.write_text(answer_content, encoding='utf-8')
            logger.info("Answer written to file: %s", output_path)

    @staticmethod
    def _build_initial_prompt(
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
        visualization_guidance: str,
    ) -> str:
        return f"""You are an expert data scientist using the DeepAnalyze model to solve data science tasks.

Task Description:
{description}

Input/Output Requirements:
{io_instructions}

Data Directory: {data_dir}
Output File: {output_path}

Visualization Policy:
{visualization_guidance}

Please use the following format to analyze and solve the problem:
1. Analyze the task in the <Analyze>...</Analyze> tags
2. Provide the code to execute in the <Code>...</Code> tags (may include ```python``` code blocks)
3. The system will provide code execution results in the <Execute>...</Execute> tags
4. When you determine that the code execution results can successfully solve the problem, output the final answer in the <Answer>...</Answer> tags

Please begin the first round of analysis."""

    async def solve(
        self,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
    ) -> None:
        """
        Execute the DeepAnalyze workflow to solve a data science task.
        
        The workflow:
        1. Sends task description to LLM
        2. Extracts and executes code from <Code> blocks
        3. Feeds execution results back via <Execute> blocks
        4. Repeats until <Answer> tag is found or max iterations reached
        5. Collects all output files from sandbox to destination
        """
        logger.info(
            "DeepAnalyzeWorkflow starting to solve task. Target output: %s",
            output_path,
        )

        if not self.workspace_service:
            raise ValueError("WorkspaceService is required for DeepAnalyzeWorkflow.")

        # Extract expected output filenames from task description
        expected_filenames = self._extract_output_filenames_from_description(description)
        if expected_filenames:
            logger.info("Expected output files from task description: %s", expected_filenames)

        # Get sandbox workdir and record initial files
        sandbox_workdir = self.workspace_service.get_path("sandbox_workdir")
        initial_files = self._get_initial_sandbox_files(sandbox_workdir)
        logger.debug("Initial sandbox files: %s", initial_files)

        initial_prompt = self._build_initial_prompt(
            description=description,
            io_instructions=io_instructions,
            data_dir=data_dir,
            output_path=output_path,
            visualization_guidance=build_visualization_instruction_text(self.visualization_policy),
        )
        conversation_history: List[Dict[str, str]] = [
            {"role": "user", "content": initial_prompt}
        ]

        final_answer_content: Optional[str] = None
        # Keep the most recent assistant segment that contained an <Answer> block,
        # since some models emit a bare </Answer> in a follow-up turn.
        last_answer_segment: Optional[str] = None
        # If the model fails to emit a <Code> block, retry within the same iteration
        # with a short nudge, up to this many times.
        no_code_retries_max: int = int(self.agent_config.get("no_code_retries", 2))

        for iteration in range(self.max_iterations):
            logger.info(
                "--- DeepAnalyze Iteration %d/%d ---",
                iteration + 1,
                self.max_iterations,
            )

            no_code_retry_count = 0
            extracted_code: Optional[str] = None
            llm_response = ""

            while True:
                response = await self.llm_service.call_messages(
                    messages=self._build_llm_messages(conversation_history),
                    max_retries=self.llm_service.config.max_retries,
                )
                llm_response = response.choices[0].message.content
                logger.debug("DeepAnalyze raw response: %s", llm_response)
                conversation_history.append({"role": "assistant", "content": llm_response})

                # Extract answer if present
                extracted_answer = self._extract_answer_from_segment(llm_response)
                if extracted_answer:
                    final_answer_content = extracted_answer
                    last_answer_segment = llm_response
                    logger.info("Extracted answer from <Answer> tag: %s", extracted_answer[:100] + "..." if len(extracted_answer) > 100 else extracted_answer)

                if self._should_terminate(llm_response, iteration):
                    break

                extracted_code = self._extract_code_from_segment(llm_response)
                if extracted_code:
                    break

                if no_code_retry_count >= no_code_retries_max:
                    logger.warning(
                        "No <Code> block found after %d retry(ies) in iteration %d, continuing to next iteration.",
                        no_code_retry_count,
                        iteration + 1,
                    )
                    break

                no_code_retry_count += 1
                logger.warning(
                    "No <Code> block found in iteration %d, retrying (%d/%d).",
                    iteration + 1,
                    no_code_retry_count,
                    no_code_retries_max,
                )
                conversation_history.append(
                    {
                        "role": "user",
                        "content": (
                            "<Feedback>\n"
                            "No <Code>...</Code> block was detected. "
                            "Please provide executable Python code inside <Code> tags so it can be run.\n"
                            "</Feedback>\n"
                        ),
                    }
                )

            if self._should_terminate(llm_response, iteration):
                break

            if not extracted_code:
                continue

            exec_result = await self.execute_op(code=extracted_code, mode="script")
            if exec_result.success:
                logger.info("Code execution succeeded in iteration %d.", iteration + 1)
                execution_output = exec_result.stdout or "Code executed successfully."
            else:
                logger.warning("Code execution failed in iteration %d.", iteration + 1)
                execution_output = f"Error during execution:\n{exec_result.stderr}"

            safe_execution_output = truncate_output(execution_output, MAX_OUTPUT_CHARS)
            execute_block = f"\n<Execute>\n{safe_execution_output}\n</Execute>\n"
            conversation_history.append({"role": "user", "content": execute_block})

            # After successful execution, collect intermediate outputs
            if exec_result.success:
                collected = self._collect_outputs_to_destination(
                    sandbox_workdir=sandbox_workdir,
                    output_path=output_path,
                    expected_filenames=expected_filenames,
                    initial_files=initial_files,
                )
                if collected:
                    logger.info("Intermediate outputs collected in iteration %d", iteration + 1)

        # Final output collection after all iterations
        logger.info("Workflow iterations complete. Performing final output collection...")
        collected = self._collect_outputs_to_destination(
            sandbox_workdir=sandbox_workdir,
            output_path=output_path,
            expected_filenames=expected_filenames,
            initial_files=initial_files,
        )

        if not collected:
            # No files were collected from sandbox
            if not final_answer_content:
                # Try to recover answer from the last assistant segment that had it.
                if last_answer_segment:
                    final_answer_content = self._extract_answer_from_segment(last_answer_segment)
                # Fallback: scan conversation history for the most recent <Answer>.
                if not final_answer_content:
                    for msg in reversed(conversation_history):
                        if msg.get("role") != "assistant":
                            continue
                        recovered = self._extract_answer_from_segment(msg.get("content", ""))
                        if recovered:
                            final_answer_content = recovered
                            break

            if final_answer_content:
                logger.info(
                    "No output files found in sandbox, but answer content recovered from <Answer>. Writing to output file."
                )
                self._write_answer_to_file(output_path, final_answer_content)
            else:
                logger.warning(
                    "DeepAnalyzeWorkflow finished but no output files found in sandbox and no <Answer> tag content extracted."
                )
        
        logger.info("DeepAnalyzeWorkflow completed. Output directory: %s", output_path.parent)
