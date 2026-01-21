"""
DSLighting 2.0 核心协议示例：智能工具选择 Agent

这个示例展示如何使用 DSLighting 2.0 的核心协议（Action, Context, Tool）
实现一个能够根据任务状态自动选择工具的 Agent。

场景：数据分析与建模任务
数据集：bike-sharing-demand
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

# ============================================================================
# 导入 DSLighting 2.0 核心协议
# ============================================================================

from dslighting import Action, Context, Tool

# ============================================================================
# 1. 定义基础工具
# ============================================================================

class DataTools:
    """数据相关工具集合"""

    @staticmethod
    def load_data(file_path: str) -> pd.DataFrame:
        """加载数据"""
        print(f"📂 Loading data from {file_path}...")
        df = pd.read_csv(file_path)
        print(f"   ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
        return df

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""
        print("🧹 Cleaning data...")

        # 删除重复行
        before = len(df)
        df = df.drop_duplicates()
        print(f"   ✓ Removed {before - len(df)} duplicate rows")

        # 处理缺失值
        missing = df.isnull().sum().sum()
        if missing > 0:
            df = df.fillna(method='ffill').fillna(method='bfill')
            print(f"   ✓ Filled {missing} missing values")

        return df

    @staticmethod
    def analyze_data(df: pd.DataFrame) -> Dict[str, Any]:
        """数据分析"""
        print("📊 Analyzing data...")

        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': {k: str(v) for k, v in df.dtypes.items()},
            'missing': df.isnull().sum().to_dict(),
            'numeric_summary': df.describe().to_dict()
        }

        print(f"   ✓ Shape: {analysis['shape']}")
        print(f"   ✓ Columns: {len(analysis['columns'])}")
        print(f"   ✓ Missing values: {sum(analysis['missing'].values())}")

        return analysis


class ModelingTools:
    """建模相关工具集合"""

    @staticmethod
    def prepare_data(df: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        """准备建模数据"""
        print(f"🎯 Preparing data for modeling (target: {target_column})...")

        # 分离特征和目标
        X = df.drop(columns=[target_column])
        y = df[target_column]

        # 识别数值特征
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()

        print(f"   ✓ Features: {len(X.columns)}")
        print(f"   ✓ Numeric features: {len(numeric_features)}")
        print(f"   ✓ Samples: {len(X)}")

        return {
            'X': X,
            'y': y,
            'numeric_features': numeric_features
        }

    @staticmethod
    def train_model(X: pd.DataFrame, y: pd.Series,
                    model_type: str = "random_forest") -> Dict[str, Any]:
        """训练模型"""
        print(f"🤖 Training {model_type} model...")

        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split

        # 简单的类别特征编码
        X_encoded = pd.get_dummies(X, drop_first=True)

        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            X_encoded, y, test_size=0.2, random_state=42
        )

        # 训练模型
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)

        # 评估
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)

        print(f"   ✓ Train score: {train_score:.4f}")
        print(f"   ✓ Test score: {test_score:.4f}")

        return {
            'model': model,
            'model_type': model_type,
            'train_score': train_score,
            'test_score': test_score
        }

    @staticmethod
    def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """评估模型"""
        print("📈 Evaluating model...")

        from sklearn.metrics import mean_squared_error, r2_score

        y_pred = model.predict(X_test)

        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred)
        }

        print(f"   ✓ RMSE: {metrics['rmse']:.4f}")
        print(f"   ✓ R²: {metrics['r2']:.4f}")

        return metrics


# ============================================================================
# 2. 将函数封装成 Tool
# ============================================================================

load_data_tool = Tool(
    name="load_data",
    description="Load data from CSV file",
    fn=DataTools.load_data
)

clean_data_tool = Tool(
    name="clean_data",
    description="Clean data",
    fn=DataTools.clean_data
)

analyze_data_tool = Tool(
    name="analyze_data",
    description="Analyze data",
    fn=DataTools.analyze_data
)

prepare_data_tool = Tool(
    name="prepare_data",
    description="Prepare data for modeling",
    fn=ModelingTools.prepare_data
)

train_model_tool = Tool(
    name="train_model",
    description="Train ML model",
    fn=lambda X, y, model_type="random_forest": ModelingTools.train_model(X, y, model_type)
)

evaluate_model_tool = Tool(
    name="evaluate_model",
    description="Evaluate model",
    fn=lambda model, X_test, y_test: ModelingTools.evaluate_model(model, X_test, y_test)
)


# ============================================================================
# 3. 实现核心 Agent - 智能工具选择器
# ============================================================================

class IntelligentToolSelector:
    """智能工具选择 Agent"""

    def __init__(self, target_column: str = "count"):
        self.target_column = target_column
        self.step = 0
        self.history = []

        # 定义工作流程
        self.workflow_steps = [
            "load_data",
            "clean_data",
            "analyze_data",
            "prepare_data",
            "train_model",
            "evaluate_model"
        ]

    def plan(self, ctx: Context) -> Action:
        """规划方法：根据当前状态选择下一个工具"""

        current_step_name = self.workflow_steps[self.step]

        print(f"\n{'='*60}")
        print(f"📍 Step {self.step + 1}/{len(self.workflow_steps)}: {current_step_name}")
        print(f"{'='*60}")

        # 根据步骤决定动作
        if current_step_name == "load_data":
            return Action(
                tool="load_data",
                args={"file_path": ctx.data.get("file_path", "data.csv")}
            )

        elif current_step_name == "clean_data":
            return Action(
                tool="clean_data",
                args={"df": ctx.state.get("current_data")}
            )

        elif current_step_name == "analyze_data":
            return Action(
                tool="analyze_data",
                args={"df": ctx.state.get("current_data")}
            )

        elif current_step_name == "prepare_data":
            return Action(
                tool="prepare_data",
                args={
                    "df": ctx.state.get("current_data"),
                    "target_column": self.target_column
                }
            )

        elif current_step_name == "train_model":
            prepared = ctx.state.get("prepared_data", {})
            return Action(
                tool="train_model",
                args={
                    "X": prepared["X"],
                    "y": prepared["y"],
                    "model_type": "random_forest"
                }
            )

        elif current_step_name == "evaluate_model":
            prepared = ctx.state.get("prepared_data", {})
            model_info = ctx.state.get("model_info", {})

            from sklearn.model_selection import train_test_split
            X_encoded = pd.get_dummies(prepared["X"], drop_first=True)
            X_train, X_test, y_train, y_test = train_test_split(
                X_encoded, prepared["y"], test_size=0.2, random_state=42
            )

            return Action(
                tool="evaluate_model",
                args={
                    "model": model_info.get("model"),
                    "X_test": X_test,
                    "y_test": y_test
                }
            )

    def execute_action(self, ctx: Context, action: Action) -> Any:
        """执行动作并更新状态"""
        tool = ctx.get_tool(action.tool)
        result = tool(**action.args)

        self.step += 1

        # 根据步骤保存关键结果
        if action.tool == "load_data":
            ctx.state["current_data"] = result

        elif action.tool == "clean_data":
            ctx.state["current_data"] = result

        elif action.tool == "analyze_data":
            ctx.state["analysis"] = result

        elif action.tool == "prepare_data":
            ctx.state["prepared_data"] = result

        elif action.tool == "train_model":
            ctx.state["model_info"] = result

        elif action.tool == "evaluate_model":
            ctx.state["metrics"] = result

        self.history.append({
            'step': self.step,
            'tool': action.tool
        })

        return result

    def run(self, ctx: Context) -> Dict[str, Any]:
        """运行完整的流程"""
        print("\n🚀 Starting Intelligent Tool Selector Agent")
        print(f"🎯 Target Column: {self.target_column}")

        while self.step < len(self.workflow_steps):
            action = self.plan(ctx)
            self.execute_action(ctx, action)

        print(f"\n{'='*60}")
        print("✅ Workflow Complete!")
        print(f"{'='*60}")

        return ctx.state


# ============================================================================
# 4. 使用 bike-sharing-demand 数据集测试
# ============================================================================

def test_with_bike_sharing():
    """使用 bike-sharing-demand 数据集测试 Agent"""

    print("\n" + "="*80)
    print("DSLighting 2.0 Example: Intelligent Tool Selection Agent")
    print("Dataset: bike-sharing-demand (sample)")
    print("="*80 + "\n")

    # 创建示例数据
    import os

    data_path = "data/bike-sample/train.csv"

    if not os.path.exists(data_path):
        print("⚠️  Creating sample data...")

        np.random.seed(42)
        n_samples = 1000

        sample_data = pd.DataFrame({
            'datetime': pd.date_range('2023-01-01', periods=n_samples, freq='H'),
            'season': np.random.choice([1, 2, 3, 4], n_samples),
            'holiday': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
            'workingday': np.random.choice([0, 1], n_samples, p=[0.3, 0.7]),
            'weather': np.random.choice([1, 2, 3], n_samples, p=[0.6, 0.3, 0.1]),
            'temp': np.random.normal(20, 10, n_samples),
            'humidity': np.random.normal(60, 20, n_samples),
            'windspeed': np.random.normal(15, 5, n_samples),
            'count': np.random.poisson(200, n_samples)
        })

        os.makedirs('data/bike-sample', exist_ok=True)
        sample_data.to_csv(data_path, index=False)

        print(f"✓ Sample data created: {data_path}")
        print(f"  Shape: {sample_data.shape}")
        print(f"  Columns: {', '.join(sample_data.columns)}\n")

    # 创建上下文
    tools = {
        'load_data': load_data_tool,
        'clean_data': clean_data_tool,
        'analyze_data': analyze_data_tool,
        'prepare_data': prepare_data_tool,
        'train_model': train_model_tool,
        'evaluate_model': evaluate_model_tool
    }

    ctx = Context(
        task="预测共享单车租赁数量",
        data={'file_path': data_path},
        tools=tools
    )

    # 创建 Agent
    agent = IntelligentToolSelector(target_column='count')

    # 运行 Agent
    final_state = agent.run(ctx)

    # 统计信息
    print("\n" + "="*60)
    print("📊 Execution Summary")
    print("="*60)
    print(f"Total Steps: {len(agent.history)}")
    print(f"Tools Used: {', '.join([h['tool'] for h in agent.history])}")

    if 'metrics' in final_state:
        print(f"\nFinal Metrics:")
        for metric, value in final_state['metrics'].items():
            print(f"  • {metric}: {value:.4f}")

    print("\n✅ Test completed successfully!")

    return final_state


# ============================================================================
# 5. 额外示例：动态工具注册
# ============================================================================

def demo_dynamic_tool_registration():
    """演示动态注册工具"""

    print("\n" + "="*80)
    print("Demo: Dynamic Tool Registration")
    print("="*80 + "\n")

    # 创建上下文
    ctx = Context(
        task="演示动态工具注册",
        data={"message": "Hello DSLighting 2.0!"},
        tools={}
    )

    # 动态创建并注册工具
    custom_tool = Tool(
        name="custom_greeter",
        description="A custom greeting tool",
        fn=lambda msg: f"Hello! {msg}"
    )

    ctx.register_tool(custom_tool)

    # 使用注册的工具
    tool = ctx.get_tool("custom_greeter")
    result = tool(ctx.data["message"])

    print(f"✓ Tool registered and used: {result}")
    print(f"✓ Available tools: {list(ctx.tools.keys())}\n")


# ============================================================================
# 6. 主函数
# ============================================================================

if __name__ == "__main__":

    # 运行主测试
    test_with_bike_sharing()

    # 运行动态工具注册演示
    demo_dynamic_tool_registration()

    print("\n" + "="*80)
    print("🎉 All examples completed successfully!")
    print("="*80)
    print("\n💡 Key Takeaways:")
    print("  1. Tool: 任何功能都可以封装成工具")
    print("  2. Context: 统一的上下文，组装数据和工具")
    print("  3. Agent: 智能选择工具，自动化工作流程")
    print("  4. 可扩展: 轻松添加新工具和新功能\n")
