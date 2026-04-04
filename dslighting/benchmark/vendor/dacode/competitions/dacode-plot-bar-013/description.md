# plot-bar-013

Analyze the ICC Hall of Fame dataset to visualize the player roles. Create a bar chart based on the format requirements in plot.yaml and

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
**Context:**

This dataset offers a detailed record of cricketers inducted into the ICC Hall of Fame, reflecting the highest honors in the sport. Spanning inductees from various eras, it provides data on their career achievements, the periods during which they were active, etc. The dataset serves as a valuable resource for cricket enthusiasts, sports historians, and researchers interested in the evolution of cricket and its legendary figures.

**Variables:**

- **profile:** URL linking to the player's profile on the ICC Hall of Fame website.
- **fname**:First name of the player.
- **lname:** Last name of the player.
- **country:** Country that the player represented in international cricket.
- **Induction:**ear the player was inducted into the Hall of Fame.
- **dob:** Date of birth of the player.
- **bowlingstyle:** Describes the player's bowling style (e.g., Right-arm fast, Left-arm spin).
- **role:** The role the player had in the team (e.g., Batsman, Bowler, All-rounder, Wicketkeeper).
- **debut:** The year the player debuted in international cricket.
- **batstyle:** The player's batting style (e.g., Left-handed, Right-handed).
- **careerstart:** Year when the player began their international cricket career.
- **careerEnd:** Year when the player retired from international cricket.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#3274a1"]
figsize: [12.0, 6.0]
graph_title: "Distribution of Player Roles in Hall of Fame"
x_label: "Player Role"
y_label: "Count"
xtick_labels: ["Batter", "All-rounder", "Bowler", "Wicket-keeper", "Right-hand"]
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
