"""
Data Science Prompt Templates

Standard prompts for data science tasks.
"""

from typing import List, Optional
from ..base import create_prompt_template, get_common_guidelines


def create_modeling_prompt(
    task_type: str,
    data_description: str,
    target_variable: str,
    requirements: Optional[List[str]] = None,
) -> str:
    """
    Create a modeling prompt for ML tasks.

    Args:
        task_type: Type of task (regression, classification, etc.)
        data_description: Description of the data
        target_variable: Name of the target variable
        requirements: Additional requirements

    Returns:
        Formatted modeling prompt
    """
    prompt_dict = {
        "Role": "You are an expert Machine Learning Engineer and Data Scientist.",
        "Task": f"Build a {task_type} model to predict '{target_variable}'.",
        "Data Information": data_description,
        "Instructions": {
            "Goal": f"Create an accurate and robust {task_type} model",
            "Approach": [
                f"Perform exploratory data analysis first",
                f"Preprocess the data appropriately",
                f"Engineer relevant features",
                f"Train and evaluate a {task_type} model",
                f"Use cross-validation",
                f"Save predictions to submission.csv",
            ],
            **get_common_guidelines()
        }
    }

    if requirements:
        prompt_dict["Instructions"]["Additional Requirements"] = requirements

    return create_prompt_template(prompt_dict)


def create_eda_prompt(
    data_description: str,
    focus_areas: Optional[List[str]] = None,
) -> str:
    """
    Create an Exploratory Data Analysis (EDA) prompt.

    Args:
        data_description: Description of the data
        focus_areas: Specific areas to focus on

    Returns:
        Formatted EDA prompt
    """
    if focus_areas is None:
        focus_areas = [
            "Data quality and missing values",
            "Distribution of variables",
            "Correlations between features",
            "Outliers and anomalies",
        ]

    prompt_dict = {
        "Role": "You are an expert Data Analyst.",
        "Task": "Perform comprehensive Exploratory Data Analysis (EDA).",
        "Data Information": data_description,
        "Instructions": {
            "Goal": "Understand the data and extract meaningful insights",
            "Analysis Areas": focus_areas,
            "Requirements": [
                "Load and inspect the data",
                "Generate summary statistics",
                "Create visualizations where helpful",
                "Identify patterns and relationships",
                "Report findings clearly",
            ],
            **get_common_guidelines()
        }
    }

    return create_prompt_template(prompt_dict)
