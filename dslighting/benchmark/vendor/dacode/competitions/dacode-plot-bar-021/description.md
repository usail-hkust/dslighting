# plot-bar-021

Based on the contents of tips.md, I need help calculating the number of positive and negative sales figures for each category among the top 250 restaurants. Positive sales are those greater than zero. Please plot this data in a bar chart according to the format specified in plot.yaml, labeling each category on the x-axis. Save the resulting image as 'category.png'

## Output Requirements

Your final output must be a submission directory.

The exact directory name will be provided at runtime in the CRITICAL I/O REQUIREMENTS section.

Inside that directory, you must create exactly these three files:

- rendered plot image artifact
- structured plot metadata JSON artifact
- numeric payload artifact extracted from the figure

---

## Dataset Background

## About Dataset

### Context
The year 2020 is behind us, therefore, many summaries of this pandemic year are created, e.g. in the form of rankings.

### Content
The data was obtained by means of web scraping, i.e. data download with the use of programming code based on the website code. In this case, the "rvest" package from the R programming language was used along with the "SelectorGadet" browser add-on to facilitate work with the website.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
figsize: [20,7]
legend_title: "Sales_year"
labels: ["positive", "negative"]
colors: ["#58D3F7","#FA5858"]
x_label: "category"
y_label: "Sales"
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
