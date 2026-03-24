# plot-scatter-004

Using the 17K Mobile Strategy Game dataset, create a scatter plot to illustrate the relationship between the time since release and user rating count. Clean the data by removing games with fewer than 200 user ratings and an update gap of less than 6 months. Reclassify the game genres, and only include games from popular genres (Puzzle, Action, Adventure, etc.). Follow the instructions in tips.txt and format according to plot.yaml. ’

## Output Requirements

You must create a **submission directory** containing exactly three files:

- `result.png` - The final rendered plot image
- `plot.json` - Structured plot metadata  
- `result.npy` - Numeric plot payload extracted from the figure

The exact directory name will be provided at runtime in the CRITICAL I/O REQUIREMENTS section.

Inside that directory, you must create exactly these three files:

- `result.png` - the final rendered plot image
- `plot.json` - structured plot metadata
- `result.npy` - numeric plot payload extracted from the figure

---

## Dataset Background

## About Dataset

# Overview

The mobile games industry is worth billions of dollars, with companies spending vast amounts of money on the development and marketing of these games to an equally large market. Using this data set, insights can be gained into a sub-market of this market, strategy games. This sub-market includes titles such as Clash of Clans, Plants vs Zombies and Pokemon GO.

# Some ideas

You could use the number of ratings as a proxy indicator for the overall success of a game, and then work out what factors make a successful game. Or you could measure the state of the market over time and try predict where it is headed.
And I think an analysis of the icons of the apps would be pretty cool

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#1f77b4"]
figsize: [16.0, 6.0],
x_label: "Updated version date since release (days)"
y_label: "User Rating count"
```

Your chart output **must** match these values exactly.

---

## Output File Format Details

### `plot.json` — Required Keys

Your `plot.json` MUST use **exactly** these keys (the same schema as `sample_plot.json` in your workspace):

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
fig.savefig(f"{output_dir}/result.png")

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
with open(f"{output_dir}/plot.json", "w") as f:
    json.dump(plot_meta, f)
```

### `result.npy` — Required Shape

Save the **primary numeric data** of the plot (bar heights, line y-values, pie sizes, scatter y-values) as a **2D array with shape `(1, N)`**, where N = number of data points:

```python
np.save(f"{output_dir}/result.npy", data_values.reshape(1, -1))
```
