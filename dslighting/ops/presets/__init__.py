"""
Workflow-specific operators and response models.

This module contains operators that are specific to certain workflows.
These operators are NOT re-exported from the main `dslighting.ops` module
to keep the general-purpose and workflow-specific operators separated.

**Usage:**
```python
# Import workflow-specific operators
from dslighting.ops.presets import (
    ScEnsembleOperator,
    AFlowReviewOperator,
    ComplexityScorerOperator,
    AutoKaggleReviewerOperator,
)

# Or import from specific workflow modules
from dslighting.ops.presets.aflow import ScEnsembleOperator
from dslighting.ops.presets.autokaggle import AutoKaggleReviewerOperator
```

**Available Operators by Workflow:**
- AFlow: ScEnsembleOperator, AFlowReviewOperator, AFlowReviseOperator
- AutoMind: ComplexityScorerOperator, PlanDecomposerOperator
- DSAgent: DevelopPlanOperator, ExecutePlanOperator, ReviseLogOperator
- AutoKaggle: TaskDeconstructionOperator, PhasePlanningOperator, StepPlanningOperator,
              DeveloperOperator, ValidatorOperator, AutoKaggleReviewerOperator,
              AutoKaggleSummarizerOperator
"""

from dslighting.ops.presets.aflow import (
    ScEnsembleOperator,
    ScEnsembleResponse,
    ReviewOperator as AFlowReviewOperator,
    ReviseOperator as AFlowReviseOperator,
    ReviseResponse,
)
from dslighting.ops.presets.automind import ComplexityScorerOperator, PlanDecomposerOperator
from dslighting.ops.presets.react import ReActOperator
from dslighting.ops.presets.dsagent import DevelopPlanOperator, ExecutePlanOperator, ReviseLogOperator
from dslighting.ops.presets.autokaggle import (
    TaskDeconstructionOperator,
    PhasePlanningOperator,
    StepPlanningOperator,
    DeveloperOperator,
    ValidatorOperator,
    AutoKaggleReviewerOperator,
    AutoKaggleSummarizerOperator,
    PhasePlanningResponse,
    ValidationResponse,
)

__all__ = [
    # AFlow operators and responses
    "ScEnsembleOperator",
    "ScEnsembleResponse",
    "AFlowReviewOperator",
    "AFlowReviseOperator",
    "ReviseResponse",
    # AutoMind operators
    "ComplexityScorerOperator",
    "PlanDecomposerOperator",
    # ReAct operator
    "ReActOperator",
    # DSAgent operators
    "DevelopPlanOperator",
    "ExecutePlanOperator",
    "ReviseLogOperator",
    # AutoKaggle operators and responses
    "TaskDeconstructionOperator",
    "PhasePlanningOperator",
    "StepPlanningOperator",
    "DeveloperOperator",
    "ValidatorOperator",
    "AutoKaggleReviewerOperator",
    "AutoKaggleSummarizerOperator",
    "PhasePlanningResponse",
    "ValidationResponse",
]
