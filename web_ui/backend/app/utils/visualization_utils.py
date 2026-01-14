# web_ui/backend/app/utils/vization_utils.py
"""
Utilities for generating intelligent descriptions for matplotlib visualizations.
"""

import re
from typing import Optional, Dict, Any

def extract_figure_info(fig) -> Dict[str, Any]:
    """
    Extract meaningful information from a matplotlib figure.

    Args:
        fig: matplotlib.figure.Figure object

    Returns:
        Dict containing figure information
    """
    info = {
        "has_title": False,
        "title": "",
        "has_suptitle": False,
        "suptitle": "",
        "num_axes": len(fig.axes),
        "chart_types": [],
        "axis_labels": {},
    }

    # Check suptitle
    if fig._suptitle:
        info["has_suptitle"] = True
        info["suptitle"] = fig._suptitle.get_text()

    # Analyze each axis
    for i, ax in enumerate(fig.axes):
        # Get title
        if ax.get_title():
            if not info["title"]:
                info["title"] = ax.get_title()
            info["has_title"] = True

        # Get axis labels
        xlabel = ax.get_xlabel()
        ylabel = ax.get_ylabel()
        if xlabel:
            info["axis_labels"][f"ax{i}_x"] = xlabel
        if ylabel:
            info["axis_labels"][f"ax{i}_y"] = ylabel

        # Detect chart type
        chart_type = detect_chart_type(ax)
        if chart_type:
            info["chart_types"].append(chart_type)

    return info


def detect_chart_type(ax) -> Optional[str]:
    """
    Detect the type of chart based on the axis properties.

    Args:
        ax: matplotlib axis object

    Returns:
        String describing the chart type
    """
    # Check for common chart types by examining the axis content
    lines = ax.get_lines()
    collections = ax.collections  # For scatter, bar charts etc.
    images = ax.images  # For imshow, heatmaps
    patches = ax.patches  # For bars, boxes etc.

    if images:
        return "heatmap/image"

    if collections:
        # Could be scatter plot, contour plot, etc.
        for col in collections:
            if hasattr(col, 'get_sizes'):
                return "scatter plot"
            if hasattr(col, 'get_array'):
                return "contour/colormesh"

    if patches and len(patches) > 1:
        # Multiple patches often indicate bar charts
        return "bar chart"

    if lines:
        # Line plot
        return "line plot"

    return "chart"


def generate_figure_description(fig, index: int) -> str:
    """
    Generate an intelligent description for a matplotlib figure.

    Args:
        fig: matplotlib.figure.Figure object
        index: Figure index

    Returns:
        String description
    """
    info = extract_figure_info(fig)

    # Start with basic info
    description_parts = []

    # Use title if available
    if info["has_suptitle"]:
        description_parts.append(info["suptitle"])
    elif info["has_title"]:
        description_parts.append(info["title"])

    # Add chart type
    if info["chart_types"]:
        chart_type = info["chart_types"][0]
        if not description_parts:
            description_parts.append(f"{chart_type.capitalize()}")

    # Add axis information
    axis_info = []
    if info["axis_labels"]:
        for key, label in info["axis_labels"].items():
            if key.endswith("_x") and label:
                axis_info.append(f"X-axis: {label}")
            elif key.endswith("_y") and label:
                axis_info.append(f"Y-axis: {label}")

    if axis_info:
        axis_desc = ", ".join(axis_info)
        description_parts.append(f"showing {axis_desc}")

    # Combine into final description
    if description_parts:
        return ". ".join(description_parts) + "."
    else:
        return f"Visualization {index + 1} - Generated chart"


def extract_statistical_insight(fig) -> str:
    """
    Try to extract statistical insights from the figure.
    This is a placeholder for future enhancement.

    Args:
        fig: matplotlib.figure.Figure object

    Returns:
        String with statistical insights
    """
    insights = []

    # Check if it's a heatmap (often used for correlations)
    for ax in fig.axes:
        if ax.images:
            insights.append("Heatmap visualization showing relationships between variables.")

        # Check for multiple subplots (might be facet grid)
        if len(fig.axes) > 1:
            insights.append("Multi-panel visualization for comparative analysis.")

        # Check for annotations
        if hasattr(ax, 'texts') and ax.texts:
            insights.append("Annotated chart with value labels.")

    return " ".join(insights) if insights else ""


def build_complete_description(fig, index: int, include_stats: bool = True) -> str:
    """
    Build a complete description for a figure, including statistical insights.

    Args:
        fig: matplotlib.figure.Figure object
        index: Figure index
        include_stats: Whether to include statistical insights

    Returns:
        Complete description string
    """
    base_desc = generate_figure_description(fig, index)

    if include_stats:
        stats = extract_statistical_insight(fig)
        if stats:
            return f"{base_desc} {stats}"

    return base_desc


# Template for enhanced auto-save code that will be injected
ENHANCED_AUTOSAVE_TEMPLATE = '''
import os
import json

# Store figure descriptions for saving with plots
_figure_descriptions = []
_original_figures = []

# Hook into figure creation to track them
import matplotlib.pyplot as plt
_original_figure = plt.figure

def tracking_figure(*args, **kwargs):
    fig = _original_figure(*args, **kwargs)
    _original_figures.append(fig)
    return fig

plt.figure = tracking_figure

# Enhanced auto-save function with intelligent descriptions
def auto_save_figures_with_descriptions():
    """
    Auto-save all matplotlib figures with intelligent descriptions.
    """
    import {utils_module} as viz_utils

    eda_dir = os.path.join(os.getcwd(), 'eda', '{eda_subdir}')
    os.makedirs(eda_dir, exist_ok=True)

    fig_nums = plt.get_fignums()
    if len(fig_nums) > 0:
        for i, fig_id in enumerate(fig_nums):
            fig = plt.figure(fig_id)

            # Only save user-created figures with content
            if fig.axes:
                timestamp = __import__('time').time()
                filename = f'plot_{{timestamp}}_{{i}}.png'
                filepath = os.path.join(eda_dir, filename)
                fig.savefig(filepath, bbox_inches='tight', dpi=100)

                # Generate intelligent description
                description = viz_utils.build_complete_description(fig, i, include_stats=True)

                # Save description to txt file
                txt_filename = filename.replace('.png', '.txt')
                txt_filepath = os.path.join(eda_dir, txt_filename)
                with open(txt_filepath, 'w') as f:
                    f.write(description)

                plt.close(fig)

# Override plt.show to auto-save
_original_show = plt.show
def show_with_save(*args, **kwargs):
    auto_save_figures_with_descriptions()

plt.show = show_with_save
'''
