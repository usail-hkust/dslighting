"""
DataProfilerOperator - 数据特征分析 Operator

这是一个 DSLighting 从来没有过的全新 Operator
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json

from dslighting.operators import Operator
from dslighting.services import LLMService
from dslighting.services.sandbox import SandboxService

logger = logging.getLogger(__name__)


class DataProfilerOperator(Operator):
    """
    数据特征分析 Operator

    功能：
    1. 读取数据文件（CSV/JSON）
    2. 自动分析数据特征（列类型、缺失值、统计信息）
    3. 使用 LLM 生成探索性分析洞察
    4. 返回结构化的数据特征报告

    这是 DSLighting 中全新的 Operator，之前不存在类似功能！
    """

    def __init__(
        self,
        llm_service: LLMService,
        sandbox_service: Optional[SandboxService] = None,
        enable_llm_insights: bool = True,
        **kwargs
    ):
        """
        初始化 DataProfilerOperator

        Args:
            llm_service: LLM 服务（用于生成数据洞察）
            sandbox_service: 沙箱服务（用于安全执行代码）
            enable_llm_insights: 是否启用 LLM 洞察分析
            **kwargs: 其他参数
        """
        super().__init__(name="DataProfilerOperator", **kwargs)
        self.llm_service = llm_service
        self.sandbox_service = sandbox_service
        self.enable_llm_insights = enable_llm_insights

        logger.info(
            f"[{self.name}] Initialized with "
            f"LLM insights={'enabled' if enable_llm_insights else 'disabled'}"
        )

    async def __call__(
        self,
        data_path: Path,
        analysis_depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        分析数据文件特征

        Args:
            data_path: 数据文件路径（CSV 或 JSON）
            analysis_depth: 分析深度 (basic, standard, deep)

        Returns:
            Dict[str, Any]: 数据特征报告
        """
        logger.info(f"[{self.name}] Starting data profiling: {data_path}")

        # 验证文件存在
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")

        # 生成分析代码
        profiling_code = self._generate_profiling_code(data_path, analysis_depth)

        # 在沙箱中执行
        if self.sandbox_service:
            exec_result = self.sandbox_service.run_script(profiling_code)

            if not exec_result.success:
                logger.error(f"[{self.name}] Execution failed: {exec_result.stderr}")
                raise RuntimeError(f"Data profiling failed: {exec_result.stderr}")

            # 解析结果
            try:
                profile_data = json.loads(exec_result.stdout)
                logger.info(f"[{self.name}] Profiling completed: {len(profile_data.get('columns', []))} columns")
            except json.JSONDecodeError as e:
                logger.error(f"[{self.name}] Failed to parse result: {e}")
                raise ValueError(f"Invalid result format: {e}")
        else:
            logger.warning(f"[{self.name}] No sandbox, executing locally")
            profile_data = self._execute_profiling_locally(data_path, analysis_depth)

        # 计算质量评分
        profile_data["quality_score"] = self._calculate_quality_score(profile_data)

        # 生成 LLM 洞察
        if self.enable_llm_insights:
            logger.info(f"[{self.name}] Generating LLM insights...")
            profile_data["insights"] = await self._generate_llm_insights(profile_data, analysis_depth)
        else:
            profile_data["insights"] = None

        logger.info(f"[{self.name}] Data profiling completed. Quality score: {profile_data['quality_score']}/100")

        return profile_data

    def _generate_profiling_code(self, data_path: Path, analysis_depth: str) -> str:
        """生成数据探索分析代码"""
        include_advanced = analysis_depth in ["standard", "deep"]
        include_correlation = analysis_depth == "deep"

        code = f"""
import pandas as pd
import json

# 加载数据
data_path = "{data_path}"
if data_path.endswith('.csv'):
    df = pd.read_csv(data_path)
elif data_path.endswith('.json'):
    df = pd.read_json(data_path)
else:
    raise ValueError(f"Unsupported file format: {{data_path}}")

# 基本信息
file_info = {{
    "path": str(data_path),
    "rows": len(df),
    "columns": len(df.columns),
    "size_mb": data_path.stat().st_size / (1024 * 1024),
}}

# 列信息
columns = []
for col in df.columns:
    col_info = {{
        "name": col,
        "dtype": str(df[col].dtype),
        "non_null_count": df[col].notna().sum(),
        "null_count": df[col].isna().sum(),
        "null_percentage": (df[col].isna().sum() / len(df)) * 100,
    }}

    if df[col].dtype in ['int64', 'float64']:
        col_info.update({{
            "type": "numeric",
            "min": float(df[col].min()) if not df[col].isna().all() else None,
            "max": float(df[col].max()) if not df[col].isna().all() else None,
            "mean": float(df[col].mean()) if not df[col].isna().all() else None,
        }})
    else:
        col_info.update({{
            "type": "categorical",
            "unique_count": df[col].nunique(),
        }})

    columns.append(col_info)

# 统计摘要
statistics = {{
    "total_cells": len(df) * len(df.columns),
    "total_null_cells": df.isna().sum().sum(),
    "null_percentage": (df.isna().sum().sum() / (len(df) * len(df.columns))) * 100,
    "duplicate_rows": int(df.duplicated().sum()),
}}

result = {{
    "file_info": file_info,
    "columns": columns,
    "statistics": statistics,
}}

print(json.dumps(result, indent=2, ensure_ascii=False))
"""
        return code

    def _execute_profiling_locally(self, data_path: Path, analysis_depth: str) -> Dict[str, Any]:
        """本地执行数据探索"""
        import pandas as pd

        if data_path.suffix == '.csv':
            df = pd.read_csv(data_path)
        elif data_path.suffix == '.json':
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {data_path.suffix}")

        return {
            "file_info": {
                "path": str(data_path),
                "rows": len(df),
                "columns": len(df.columns),
            },
            "columns": [
                {"name": col, "dtype": str(df[col].dtype)}
                for col in df.columns
            ],
            "statistics": {},
        }

    def _calculate_quality_score(self, profile_data: Dict[str, Any]) -> float:
        """计算数据质量评分"""
        score = 100.0
        null_pct = profile_data["statistics"].get("null_percentage", 0)
        score -= min(null_pct * 0.5, 20)
        return max(0.0, min(100.0, score))

    async def _generate_llm_insights(self, profile_data: Dict[str, Any], analysis_depth: str) -> Dict[str, str]:
        """使用 LLM 生成数据洞察"""
        prompt = f"""
Analyze this data profile:

File: {profile_data['file_info']['path']}
Rows: {profile_data['file_info']['rows']}
Columns: {profile_data['file_info']['columns']}
Quality Score: {profile_data['quality_score']:.1f}/100

Missing Values: {profile_data['statistics']['null_percentage']:.2f}%
Duplicate Rows: {profile_data['statistics']['duplicate_rows']}

Provide:
1. Data Quality Assessment
2. Potential Issues
3. Recommendations

Respond as JSON with keys: quality_assessment, potential_issues, recommendations
"""

        try:
            response = await self.llm_service.call(prompt)
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw_response": response}
        except Exception as e:
            logger.error(f"[{self.name}] Failed to generate insights: {e}")
            return {"error": str(e)}
