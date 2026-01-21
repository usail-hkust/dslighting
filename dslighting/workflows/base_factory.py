"""
Base Workflow Factory - Base class for all Workflow Factory

Provides standard MLE task loading functionality, users don't need to reimplement
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseWorkflowFactory(ABC):
    """
    Base class for Workflow Factory

    Provides:
    1. Standard LLM/Sandbox/Workspace service creation
    2. Standard MLE task loading (from registry)
    3. run_with_task_id() convenience method

    Users only need to:
    1. Inherit from BaseWorkflowFactory
    2. Implement create_agent() method
    3. Define their own workflow class
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        timeout: int = 300,
        keep_workspace: bool = False,
        **agent_init_kwargs
    ):
        """
        Initialize factory

        Args:
            model: LLM model name
            api_key: API key (optional, read from env var if not provided)
            api_base: API base URL (optional, read from env var if not provided)
            provider: LLM provider (optional)
            temperature: Temperature parameter (optional, read from env var if not provided)
            timeout: Sandbox timeout
            keep_workspace: Whether to keep workspace
            **agent_init_kwargs: Additional parameters, will be passed to create_agent()

        Note:
            Use DSLighting's ConfigBuilder to automatically read config from environment variables:
            - API_KEY, API_BASE, LLM_MODEL
            - LLM_MODEL_CONFIGS (multi-model config)

        Example:
            >>> factory = MyWorkflowFactory(
            ...     model="gpt-4o",
            ...     max_iterations=3,  # Passed to create_agent()
            ...     use_data_insights=True
            ... )
        """
        self.model = model
        self.timeout = timeout
        self.keep_workspace = keep_workspace
        self._agent_init_kwargs = agent_init_kwargs

        # Use DSLighting's ConfigBuilder to automatically read config from environment variables
        from dslighting.core.config_builder import ConfigBuilder
        config_builder = ConfigBuilder()
        config = config_builder.build_config(
            model=model,
            api_key=api_key,
            api_base=api_base,
            provider=provider,
            temperature=temperature,
        )

        # Extract LLM config from configuration
        llm_config = config.llm

        # Create services (infrastructure ready, users don't need to care)
        from dslighting.services import LLMService, SandboxService, WorkspaceService

        self.llm_service = LLMService(config=llm_config)
        self.workspace_service = WorkspaceService(
            run_name=f"{self._get_workflow_name()}_{model.replace('/', '_')}"
        )
        self.sandbox_service = SandboxService(
            workspace=self.workspace_service,
            timeout=timeout
        )

        logger.debug(f"{self.__class__.__name__} initialized")
        logger.debug(f"  - Model: {model}")
        logger.debug(f"  - Timeout: {timeout}s")
        logger.debug(f"  - Keep workspace: {keep_workspace}")

    def _get_workflow_name(self) -> str:
        """
        Get workflow 名称（用于日志和 workspace 命名）

        子class可以重写此method以Provide自define名称
        """
        return self.__class__.__name__.replace("Factory", "").lower()

    @abstractmethod
    def create_agent(self, **kwargs) -> Any:
        """
        Create Agent instance（子classmustimplement/implementation）

        Args:
            **kwargs: Agent ConfigParameter

        Returns:
            Agent instance
        """
        raise NotImplementedError("Subclasses must implement create_agent()")

    def cleanup(self):
        """Cleanup workspace"""
        if not self.keep_workspace:
            self.workspace_service.cleanup()
            logger.debug(f"✓ Workspace cleaned")

    def run(
        self,
        data=None,
        task_id: Optional[str] = None,
        data_dir: Optional[Path] = None,
        **kwargs
    ):
        """
        Run workflow - 统一的入口（recommended）

        这是synchronous method，userno need/don't need关心 async/await

        Supports multiplecalling modes：

        1. **使用 LoadedData object**（simplest）:
           >>> data = dslighting.load_data("/path/to/data")
           >>> result = factory.run(data)  # ← 不need/require await

        2. **使用 task_id**:
           >>> result = factory.run(task_id="bike-sharing-demand")

        3. **使用 task_id + data_dir**:
           >>> result = factory.run(
           ...     task_id="bike-sharing-demand",
           ...     data_dir="/path/to/data"
           ... )

        4. **使用 dataset dict/dictionary**（从 datasets.load_xxx() Return的）:
           >>> dataset = dslighting.datasets.load_bike_sharing_demand()
           >>> result = factory.run(dataset)

        Args:
            data: Optional，可以是：
                - LoadedData object（从 dslighting.load_data() Return）
                - dataset dict/dictionary（从 dslighting.datasets.load_xxx() Return）
                - IfProvide，将从中提取 task_id 和 data_dir
            task_id: Task ID（e.g. "bike-sharing-demand"）
                - If不Provide且 data 也不Provide，need/require单独指定 data_dir
            data_dir: data directoryPath
            **kwargs: Pass给 create_agent() 的Parameter

        Returns:
            Executeresult

        Example:
            >>> factory = MyWorkflowFactory(model="gpt-4o")

            >>> # 方式 1: 使用 LoadedData（不need/require await）
            >>> data = dslighting.load_data("/path/to/data")
            >>> result = factory.run(data)

            >>> # 方式 2: 使用 task_id（不need/require await）
            >>> result = factory.run(task_id="bike-sharing-demand")

            >>> # 方式 3: 使用 dataset dict/dictionary（不need/require await）
            >>> dataset = dslighting.datasets.load_bike_sharing_demand()
            >>> result = factory.run(dataset)
        """
        import asyncio
        return asyncio.run(self._run_async(data=data, task_id=task_id, data_dir=data_dir, **kwargs))

    async def _run_async(
        self,
        data=None,
        task_id: Optional[str] = None,
        data_dir: Optional[Path] = None,
        **kwargs
    ):
        """
        Run workflow - 统一的入口（recommended）

        Supports multiplecalling modes：

        1. **使用 LoadedData object**（simplest）:
           >>> data = dslighting.load_data("/path/to/data")
           >>> await factory.run(data)

        2. **使用 task_id**:
           >>> await factory.run(task_id="bike-sharing-demand")

        3. **使用 task_id + data_dir**:
           >>> await factory.run(
           ...     task_id="bike-sharing-demand",
           ...     data_dir="/path/to/data"
           ... )

        4. **使用 dataset dict/dictionary**（从 datasets.load_xxx() Return的）:
           >>> dataset = dslighting.datasets.load_bike_sharing_demand()
           >>> await factory.run(dataset)

        Args:
            data: Optional，可以是：
                - LoadedData object（从 dslighting.load_data() Return）
                - dataset dict/dictionary（从 dslighting.datasets.load_xxx() Return）
                - IfProvide，将从中提取 task_id 和 data_dir
            task_id: Task ID（e.g. "bike-sharing-demand"）
                - If不Provide且 data 也不Provide，need/require单独指定 data_dir
            data_dir: data directoryPath
            **kwargs: Pass给 create_agent() 的Parameter

        Example:
            >>> factory = MyWorkflowFactory(model="gpt-4o")

            >>> # 方式 1: 使用 LoadedData
            >>> data = dslighting.load_data("/path/to/data")
            >>> await factory.run(data)

            >>> # 方式 2: 使用 task_id
            >>> await factory.run(task_id="bike-sharing-demand")

            >>> # 方式 3: 使用 dataset dict/dictionary
            >>> dataset = dslighting.datasets.load_bike_sharing_demand()
            >>> await factory.run(dataset)
        """
        # 情况 1: Provide了 data Parameter
        if data is not None:
            # Check data 的type
            if hasattr(data, 'task_id') and hasattr(data, 'data_dir'):
                # LoadedData object
                logger.info(f"✓ 检测到 LoadedData object")
                task_id = data.task_id
                data_dir = data.data_dir
            elif isinstance(data, dict) and 'data_dir' in data:
                # dataset dict/dictionary（从 dslighting.datasets.load_xxx() Return）
                logger.info(f"✓ 检测到 dataset dict/dictionary")
                data_dir = Path(data['data_dir'])
                task_id = task_id or data.get('task_id')
            else:
                raise ValueError(
                    f"不支持的 data type: {type(data)}\n"
                    f"期望: LoadedData object或 dataset dict/dictionary"
                )

        # 情况 2: 只Provide了 task_id
        elif task_id is not None and data_dir is None:
            # 从 registry automatic/automatically查找 data_dir
            logger.info(f"✓ 只Provide task_id，将从 registry automatic/automatically查找 data_dir")
            # 调用 run_with_task_id，让它的内部逻辑Process data_dir 查找
            return await self.run_with_task_id(task_id=task_id, **kwargs)

        # 情况 3: mustProvide task_id 和 data_dir
        if task_id is None:
            raise ValueError("mustProvide task_id Parameter（orProvidecontains task_id 的 data object）")
        if data_dir is None:
            raise ValueError("mustProvide data_dir Parameter（orProvidecontains data_dir 的 data object）")

        # 调用 run_with_task_id
        return await self.run_with_task_id(
            task_id=task_id,
            data_dir=Path(data_dir) if not isinstance(data_dir, Path) else data_dir,
            **kwargs
        )

    async def run_with_task_id(
        self,
        task_id: str,
        data_dir: Optional[Path] = None,
        task_loader: Optional[Any] = None,
        output_path: Optional[Path] = None,
        **agent_kwargs
    ) -> None:
        """
        使用 task_id Run workflow（class似 DSLighting 的 run_agent）

        这是推荐的用法 - automatic/automatically从 registry Loadstandard MLE formatConfig

        Args:
            task_id: Task ID（e.g. "bike-sharing-demand"）
            data_dir: Optional的data directoryPath。If不Provide，将从 registry automatic/automatically查找
            task_loader: Optional的TaskLoad器。If不Provide，使用 MLETaskLoader
            output_path: Optional的OutputFilePath。If不Provide，使用 task_loader Return的defaultPath
            **agent_kwargs: Pass给 create_agent() 的Parameter（e.g. max_iterations）

        Example:
            >>> factory = MyWorkflowFactory(model="gpt-4o")
            >>> await factory.run_with_task_id("bike-sharing-demand", max_iterations=3)

            >>> # 指定OutputFile名
            >>> await factory.run_with_task_id("bike-sharing-demand", output_path="my_submission.csv")
        """
        logger.info(f"=" * 80)
        logger.info(f"运行 {self.__class__.__name__} with task_id")
        logger.info(f"=" * 80)
        logger.info(f"  Task ID: {task_id}")
        logger.info(f"  Agent Config: {agent_kwargs}")
        logger.info(f"=" * 80)

        # ✅ 使用 Task Loader LoadTask（从 tasks 层）
        if task_loader is None:
            from dslighting.tasks import MLETaskLoader
            task_loader = MLETaskLoader()

        # ✅ 对于 MLE format，只Analyze public Data（避免泄露 private/test_answer.csv）
        public_dir = data_dir / "prepared" / "public"

        if not public_dir.exists():
            logger.error(f"❌ Public data directory not found: {public_dir}")
            logger.error(f"Expected structure: {data_dir}/prepared/public/train.csv")
            raise FileNotFoundError(
                f"Public data directory not found: {public_dir}\n"
                f"Expected structure: {data_dir}/prepared/public/train.csv"
            )

        logger.info(f"✓ 使用 public data directory（避免泄露answer）: {public_dir}")

        # Loadstandard MLE formatTaskConfig（Pass public_dir 而不是 data_dir）
        description, io_instructions, _, default_output_path = task_loader.load_task(
            task_id=task_id,
            data_dir=public_dir  # ✅ 只Analyze public 目录
        )

        # ✅ IfuserProvide了 output_path，使用user的；Otherwise使用default的
        output_path = output_path or default_output_path

        # ✅ VerifyLoadresult
        logger.info(f"✓ TaskLoadcompleted:")
        logger.info(f"  - Description 长度: {len(description)} 字符")
        logger.info(f"  - I/O Instructions 长度: {len(io_instructions)} 字符")
        logger.info(f"  - Public 目录: {public_dir}")
        logger.info(f"  - OutputPath: {output_path}")

        # ✅ automatic/automaticallyProcessData链接（Base设施层，userno need/don't need关心）
        # 将 public_dir 的内容链接到 sandbox 根目录
        logger.info(f"✓ automatic/automatically链接 public Data到 sandbox...")
        logger.info(f"  源目录: {public_dir}")
        self.workspace_service.link_data_to_workspace(public_dir)
        logger.info(f"  ✓ Sandbox 已准备就绪")

        # ✅ Check io_instructions 是否完整（shouldcontains "CRITICAL I/O REQUIREMENTS"）
        if len(io_instructions) < 100 or "CRITICAL I/O" not in io_instructions:
            logger.warning(f"⚠️ I/O Instructions 可能不完整！长度: {len(io_instructions)}")
            logger.warning(f"  io_instructions 前200字符: {io_instructions[:200]}")
            logger.warning(f"  这可能导致Model无法correct理解FilePath要求！")
            logger.warning(f"  尝试重新Generate完整的 I/O instructions...")

            # ✅ 尝试重新Generate完整的 I/O instructions
            try:
                from dsat.services.data_analyzer import DataAnalyzer
                analyzer = DataAnalyzer()
                io_instructions = analyzer.generate_io_instructions(
                    output_path.name,
                    optimization_context=False
                )
                logger.info(f"✓ 重新Generate I/O instructions success！长度: {len(io_instructions)}")
            except Exception as e:
                logger.error(f"重新Generatefailed: {e}")
                # Finally的回退：使用硬编码的format
                io_instructions = f"""
--- CRITICAL I/O REQUIREMENTS ---

You MUST follow these file system rules precisely. Failure to do so will cause a fatal error.

1. **INPUT DATA:**
   - All input files are located in the **current working directory** (./).
   - Example: Use `pd.read_csv('train.csv')`.

2. **OUTPUT FILE:**
   - You MUST save your final submission file to the **current working directory** (./).
   - The required output filename is: `{output_path.name}`
   - **Correct Example:** `submission_df.to_csv('{output_path.name}', index=False)`

**IMPORTANT:** These path requirements are non-negotiable and must be followed exactly.
"""

        # Create agent（合并 __init__ 时保存的Parameter和运行时Parameter）
        all_agent_kwargs = {**self._agent_init_kwargs, **agent_kwargs}
        agent = self.create_agent(**all_agent_kwargs)

        # ✅ 记录开始时间（用于计算 duration）
        import time
        start_time = time.time()

        # Run workflow（Pass public_dir 给 workflow）
        await agent.solve(
            description=description,
            io_instructions=io_instructions,  # ✅ containsOutputFile名要求
            data_dir=public_dir  # ✅ 只Pass public 目录给 workflow
        )

        # ✅ 计算Execute时间
        duration = time.time() - start_time

        # ✅ automatic/automaticallyGrading（Base设施，userno need/don't need关心）
        logger.info(f"\n{'='*80}")
        logger.info(f"automatic/automaticallyGrading中...")
        logger.info(f"{'='*80}")

        score = None
        try:
            # Get提交FilePath
            submission_file = self.workspace_service.get_path("sandbox_workdir") / output_path.name

            if submission_file.exists():
                logger.info(f"✓ 提交File: {submission_file}")

                # ✅ 通用Grading逻辑：尝试多种方式Load benchmark
                benchmark = None
                benchmark_loaded = False

                # 方式 1: Check task_loader 是否有 load_benchmark method
                if hasattr(task_loader, 'load_benchmark'):
                    try:
                        logger.info(f"尝试使用 task_loader.load_benchmark()...")
                        benchmark = task_loader.load_benchmark(
                            task_id=task_id,
                            data_dir=data_dir
                        )
                        if benchmark:
                            benchmark_loaded = True
                            logger.info(f"✓ 通过 task_loader Load benchmark")
                    except Exception as e:
                        logger.warning(f"task_loader.load_benchmark() failed: {e}")

                # Fallback 2: Try loading directly from benchmarks/mlebench
                if not benchmark_loaded:
                    try:
                        logger.info(f"Attempting to load directly from benchmark/mlebench...")
                        from pathlib import Path as LibPath
                        benchmarks_dir = LibPath(__file__).parent.parent.parent / "benchmark" / "mlebench"
                        from dslighting.benchmark.mlebench.registry import Registry

                        registry = Registry(benchmarks_dir)
                        competition = registry.get_competition(task_id)

                        if competition:
                            # Create simple benchmark wrapper
                            class DirectBenchmark:
                                def __init__(self, comp):
                                    self.competition = comp

                                async def grade(self, submission_path: str):
                                    from dslighting.benchmark.mlebench.grade import grade_csv
                                    report = grade_csv(LibPath(submission_path), self.competition)
                                    return {
                                        'score': report.score,
                                        'valid_submission': report.valid_submission
                                    }

                            benchmark = DirectBenchmark(competition)
                            benchmark_loaded = True
                            logger.debug(f"Loaded benchmark directly from MLE-Bench")
                    except Exception as e:
                        logger.warning(f"Failed to load MLE-Bench directly: {e}")

                # Fallback 3: Use universal grading (check file format)
                if not benchmark_loaded:
                    logger.info(f"Using universal grading logic...")
                    try:
                        import pandas as pd
                        # Check if file can be read normally
                        df = pd.read_csv(submission_file)
                        logger.info(f"Valid submission file: {len(df)} rows")

                        # Universal grading: file exists and is readable = success
                        # (Cannot calculate real score without ground truth)
                        score = 0.0
                        logger.info(f"Universal grading: file valid but cannot calculate real score (requires ground truth)")
                        logger.info(f"Tip: Implement task_loader.load_benchmark() method to get real score")
                    except Exception as e:
                        logger.warning(f"Universal grading failed: {e}")

                # If benchmark was successfully loaded, use it for grading
                if benchmark_loaded and benchmark and hasattr(benchmark, 'grade'):
                    try:
                        # Call benchmark.grade() for grading
                        grade_result = await benchmark.grade(
                            submission_path=str(submission_file)
                        )

                        # Extract score (grade_result may be dict or object)
                        if isinstance(grade_result, dict):
                            score = grade_result.get('score', grade_result.get('metric', 0.0))
                        else:
                            score = float(grade_result) if grade_result is not None else 0.0

                        logger.info(f"Auto-grading completed | Score: {score}")
                    except Exception as e:
                        logger.warning(f"Benchmark grading failed: {e}")
                        logger.warning(f"   Will fall back to universal grading")
                        score = 0.0
            else:
                logger.warning(f"Submission file not found: {submission_file}")
                logger.warning(f"   Workflow execution failed, cannot grade")

        except Exception as e:
            logger.warning(f"Auto-grading failed: {e}")
            logger.warning(f"   Please check submission file format and benchmark configuration")

        logger.info(f"{'='*80}\n")

        # ✅ 构建resultobject
        from types import SimpleNamespace
        result = SimpleNamespace()

        # 判断success与否：提交File存在且有Grading
        result.score = score if score is not None else 0.0
        result.success = score is not None
        result.error = None if score is not None else "Grading failed or submission not found"

        # Get成本（从 LLM service）
        result.cost = self.llm_service.get_total_cost() if hasattr(self.llm_service, 'get_total_cost') else 0.0
        result.duration = duration

        logger.info(f"=" * 80)
        logger.info(f"✓ Workflow completed")
        logger.info(f"  - Success: {result.success}")
        logger.info(f"  - Score: {result.score}")
        logger.info(f"  - Cost: ${result.cost:.4f}")
        logger.info(f"  - Duration: {result.duration:.2f}s")
        logger.info(f"=" * 80)

        # ✅ Returnresultobject
        return result
