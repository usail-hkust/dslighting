# plot-scatter-001

Analyze the Netflix dataset (`netflix.csv`). For each genre, find the title(s) with the **highest IMDb score** in that genre. If multiple titles tie for the maximum score in a genre, include **all of them**. Plot each selected title as a scatter point (x = sequential index, y = IMDb score), colored by genre.

**Important:** Compute the actual values from the data. Do NOT use hardcoded or synthetic values.

## Output Requirements

You must create a **submission directory** containing exactly three files:

- rendered plot image artifact
- structured plot metadata JSON artifact
- numeric payload artifact extracted from the figure

The exact directory name will be provided at runtime in the CRITICAL I/O REQUIREMENTS section.

---

## Dataset Background

## About Dataset
Here's a brief description of each column:

1. **title:** The title of the movie or TV show.
2. **genre:** The category or type of content, indicating its theme or style.
3. **premiere:** The date when the movie or TV show was first released or premiered.
4. **runtime:** The duration of the movie or TV show in minutes.
5. **imdb_score:** The rating of the movie or TV show on the IMDb (Internet Movie Database) platform.
6. **language:** The language in which the movie or TV show is primarily spoken or produced.
7. **year:** The year when the movie or TV show was released or premiered.

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

### Metadata JSON — Required Keys

The metadata JSON artifact MUST use **exactly** these keys (the same schema as the sample metadata file in your workspace):

```json
{
  "type":         "<chart type: bar | line | pie | scatter>",
  "color":        ["<hex color per bar/slice/line, e.g. \"#1f77b4\">"],
  "figsize":      [<width_float>, <height_float>],
  "graph_title":  "<plot title string>",
  "legend_title": "<legend title or empty string \"\">",
  "labels":       ["<series labels — often empty list []>"],
  "x_label":      "<x-axis label string>",
  "y_label":      "<y-axis label string>",
  "xtick_labels": ["<x-axis tick labels as strings>"],
  "ytick_labels": ["<y-axis tick labels as strings>"]
}
```

For scatter plots, extract colors and labels from `ax.collections` (one entry per `ax.scatter()` call = one per genre):

```python
import matplotlib
import matplotlib.pyplot as plt
import json, numpy as np

fig, ax = plt.subplots(figsize=(...))
# --- your plotting code here ---
fig.savefig("<rendered_plot_artifact_path>")

# Extract plot metadata
plot_meta = {
    "type": "scatter",
    "color": [
        matplotlib.colors.to_hex(c.get_facecolor()[0])
        for c in ax.collections
    ],
    "figsize":      list(fig.get_size_inches()),
    "graph_title":  ax.get_title(),
    "legend_title": (
        ax.get_legend().get_title().get_text()
        if ax.get_legend() else ""
    ),
    "labels":       [c.get_label() for c in ax.collections],
    "x_label":      ax.get_xlabel(),
    "y_label":      ax.get_ylabel(),
    "xtick_labels": [t.get_text() for t in ax.get_xticklabels()],
    "ytick_labels": [t.get_text() for t in ax.get_yticklabels()],
}
with open("<metadata_json_artifact_path>", "w") as f:
    json.dump(plot_meta, f)
```

### Numeric Payload — Required Shape

For scatter plots, save the **x and y coordinate pairs** as a **2D array with shape `(N, 2)`**, where N = number of scatter points:

```python
# x_values: sequential indices (0, 1, 2, ..., N-1) — the scatter point positions on x-axis
# y_values: the corresponding y-axis values (IMDb scores)
x_values = np.arange(len(best))        # shape (N,)
y_values = best['imdb_score'].values   # shape (N,)
data_values = np.column_stack([x_values, y_values])  # shape: (N, 2)
np.save("<numeric_payload_artifact_path>", data_values)
```
