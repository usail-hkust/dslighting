from typing import Optional
from pathlib import Path
import os
import logging
from .llm_factory import get_llm

logger = logging.getLogger(__name__)

async def generate_grading_rubric(task_description: str) -> str:
    """
    Uses an LLM to generate a structured grading rubric for an open-ended task.
    """
    system_prompt = """You are an expert Evaluator for complex problem-solving tasks.
Your goal is to create a clear, objective, and scoring-ready Grading Rubric (0.0 to 1.0) for an open-ended task based on its description.

## Evaluation Philosophy

The rubric should be **TASK-CENTERED**, not process-centered. Focus on:
1. **Problem Understanding** - Does the solution address the actual problem?
2. **Approach Quality** - Is the proposed solution reasonable and well-thought-out?
3. **Execution Quality** - Is the implementation correct and complete?
4. **Result Effectiveness** - Does the final output solve the problem?

## Rubric Structure

Generate 4-6 criteria based on the task nature. Use these guideline categories:

### For Analytical/Data Tasks:
1. **Problem Analysis & Approach** (Weight: 0.2-0.3)
   - Clear understanding of the problem
   - Reasonable task decomposition (if multi-step)
   - Appropriate methodology chosen

2. **Data Handling & Processing** (Weight: 0.2-0.3)
   - Data loaded and processed correctly
   - Edge cases handled appropriately
   - Data quality issues addressed

3. **Solution Implementation** (Weight: 0.3-0.4)
   - Code correctness and completeness
   - Logical flow and structure
   - Error handling

4. **Results & Validation** (Weight: 0.2-0.3)
   - Results answer the original question
   - Outputs are well-formatted and interpretable
   - Reasonable performance/accuracy achieved

### For Creative/Open-Ended Tasks:
1. **Conceptualization & Planning** (Weight: 0.2-0.3)
2. **Execution & Craftsmanship** (Weight: 0.3-0.4)
3. **Innovation & Creativity** (Weight: 0.2-0.3)
4. **Communication & Presentation** (Weight: 0.1-0.2)

## Output Format

Structure your response in Markdown:

```markdown
# Grading Rubric

## Core Criteria (Total: 1.0)

1. **Criterion Name** (Weight: 0.X)
   - [ ] Specific requirement 1
   - [ ] Specific requirement 2
   - [ ] Specific requirement 3

2. **Criterion Name** (Weight: 0.X)
   ...

## Scoring Guidelines
- **Full Credit** (100% of criterion weight): All requirements met with high quality
- **Partial Credit** (50-80%): Some requirements met or quality acceptable but not excellent
- **No Credit** (0%): Requirements not met or major issues

## Overall Assessment
After scoring all criteria, provide:
- Total Score: Sum of all criterion scores (0.0 to 1.0)
- Strengths: What went well
- Areas for Improvement: What could be better
```

**CRITICAL**:
- Tailor criteria to match the SPECIFIC task description
- Avoid generic ML pipeline criteria unless the task explicitly requires them
- Focus on OUTCOMES and SOLUTION QUALITY, not just following steps
- Make criteria measurable and objective
- Ensure all weights sum to 1.0
"""

    user_prompt = f"""Task Description:

{task_description}

Based on this task description, please generate a comprehensive grading rubric.

Requirements:
1. Analyze what this task is actually trying to achieve
2. Identify the key aspects that should be evaluated
3. Create 4-6 specific, measurable criteria
4. Assign appropriate weights (sum = 1.0)
5. Provide clear requirements for each criterion

Generate the rubric now."""

    try:
        llm_service = get_llm()
        response = await llm_service.achat(messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        return response
    except Exception as e:
        logger.error(f"Failed to generate rubric: {e}")
        return "# Grading Rubric\n\n*Failed to generate rubric automatically. Please edit this manually.*"
