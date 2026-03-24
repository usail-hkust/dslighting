# plot-scatter-001

You are tasked with analyzing the Netflix dataset. Identify the countries with the most titles in each genre and plot the results in a scatter graph. Follow the format specified in plot.yaml and

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

Here's a brief description of each column:

1. **Title:** The title of the movie or TV show.
2. **Genre:** The category or type of content, indicating its theme or style.
3. **Premiere:** The date when the movie or TV show was first released or premiered.
4. **Runtime:** The duration of the movie or TV show in minutes.
5. **IMDb Score:** The rating of the movie or TV show on the IMDb (Internet Movie Database) platform, representing its overall quality as rated by users.
6. **Language:** The language in which the movie or TV show is primarily spoken or produced.
7. **Year:** The year when the movie or TV show was released or premiered.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
figsize: [30.0, 20.0]
graph_title: "IMDb Score vs Genre"
legend_title: "Genre"
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
