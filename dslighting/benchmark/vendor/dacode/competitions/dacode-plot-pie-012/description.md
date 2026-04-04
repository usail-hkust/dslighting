# plot-pie-012

Create a list of the top 10 highest-grossing movies of all time and visualize their box office revenues as segments in a pie chart formatted as per plot.yaml. Ensure the legend includes movie names and

## Output Requirements

Your final output must be a submission directory.

The exact directory name will be provided at runtime in the CRITICAL I/O REQUIREMENTS section.

Inside that directory, you must create exactly these three files:

- rendered plot image artifact
- structured plot metadata JSON artifact
- numeric payload artifact extracted from the figure

---

## Dataset Background

### Context
This Dataset contains the data of market analysis built on The Numbers unique categorization system, which uses 6 different criteria to identify a movie. All movies released since 1995 are categorized according to the following attributes: Creative type (factual, contemporary fiction, fantasy etc.), Source (book, play, original screenplay etc.), Genre (drama, horror, documentary etc.), MPAA rating, Production method (live action, digital animation etc.) and Distributor. In order to provide a fair comparison between movies released in different years, all rankings are based on ticket sales, which are calculated using average ticket prices announced by the MPAA in their annual state of the industry report.

### Content
The Dataset contains various files illustrating statistics such as annual ticket sales, highest grossers each year since 1995, top grossing creative types, top grossing distributors, top grossing genres, top grossing MPAA ratings, top grossing sources, top grossing production methods and the number of wide releases each year

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#2ca02c", "#7f7f7f", "#9467bd", "#1f77b4", "#e377c2", "#d62728", "#17becf", "#bcbd22", "#ff7f0e", "#8c564b"]
figsize: [20.0, 12.0]
graph_title: "Top 10 Highest Grossing Movies of All Time"
```

Your chart output **must** match these values exactly.

---

## Output File Format Details

### Metadata JSON — Required Keys

The metadata JSON artifact MUST use **exactly** these keys (the same schema as the sample metadata file in your workspace):

```json
{
  "type":         "<chart type: bar | line | pie | scatter>",
  "color":        ["<hex color per bar/slice/line, e.g. "#1f77b4">"],
  "figsize":      [<width_float>, <height_float>],
  "graph_title":  "<plot title string>",
  "legend_title": "<legend title or empty string "">",
  "labels":       ["<series labels — often empty list []>"],
  "x_label":      "<x-axis label string>",
  "y_label":      "<y-axis label string>",
  "xtick_labels": ["<x-axis tick labels as strings>"],
  "ytick_labels": ["<y-axis tick labels as strings>"]
}
```

Extract these values directly from your matplotlib figure **after** rendering:

```python
import matplotlib
import matplotlib.pyplot as plt
import json, numpy as np

fig, ax = plt.subplots(figsize=(...))
# --- your plotting code here ---
fig.savefig("<rendered_plot_artifact_path>")

# Extract plot metadata
plot_meta = {
    "type": "bar",          # set to: bar | line | pie | scatter
    "color": [
        matplotlib.colors.to_hex(p.get_facecolor())
        for p in ax.patches  # use ax.lines / ax.collections for line/scatter
    ],
    "figsize":      list(fig.get_size_inches()),
    "graph_title":  ax.get_title(),
    "legend_title": (
        ax.get_legend().get_title().get_text()
        if ax.get_legend() else ""
    ),
    "labels":       [],
    "x_label":      ax.get_xlabel(),
    "y_label":      ax.get_ylabel(),
    "xtick_labels": [t.get_text() for t in ax.get_xticklabels()],
    "ytick_labels": [t.get_text() for t in ax.get_yticklabels()],
}
with open("<metadata_json_artifact_path>", "w") as f:
    json.dump(plot_meta, f)
```

### Numeric Payload — Required Shape

Save the **primary numeric data** of the plot (bar heights, line y-values, pie sizes, scatter y-values) as a **2D array with shape `(1, N)`**, where N = number of data points:

```python
np.save("<numeric_payload_artifact_path>", data_values.reshape(1, -1))
```
