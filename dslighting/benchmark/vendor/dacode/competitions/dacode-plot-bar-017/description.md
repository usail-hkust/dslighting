# plot-bar-017

Plot the total donations to each political party as a bar chart and . The image should have a size of (14, 8), with the title 'Total Denominations by Political Party', x-axis labeled as 'Total Denominations', and y-axis labeled as 'Political Party'

## Output Requirements

Your final output must be a submission directory.

The exact directory name will be provided at runtime in the CRITICAL I/O REQUIREMENTS section.

Inside that directory, you must create exactly these three files:

- rendered plot image artifact
- structured plot metadata JSON artifact
- numeric payload artifact extracted from the figure

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#87ceeb"]
figsize: [14.0, 8.0]
graph_title: "Total Denominations by Political Party"
x_label: "Total Denominations"
y_label: "Political Party"
ytick_labels: ["ALL INDIA ANNA DRAVIDA MUNNETRA KAZHAGAM", "BHARAT RASHTRA SAMITHI", "BHARATIYA JANATA PARTY", "PRESIDENT, ALL INDIA CONGRESS COMMITTEE", "SHIVSENA", "TELUGU DESAM PARTY", "YSR  CONGRESS PARTY  (YUVAJANA SRAMIKA RYTHU CONGRESS PARTY)", "DRAVIDA MUNNETRA KAZHAGAM (DMK)", "JANATA DAL ( SECULAR )", "NATIONALIST CONGRESS PARTY MAHARASHTRA PRADESH", "ALL INDIA TRINAMOOL CONGRESS", "BIHAR PRADESH JANTA DAL(UNITED)", "RASHTRIYA JANTA DAL", "AAM AADMI PARTY", "ADYAKSHA SAMAJVADI PARTY", "SHIROMANI AKALI DAL", "JHARKHAND MUKTI MORCHA", "JAMMU AND KASHMIR NATIONAL CONFERENCE", "BIJU JANATA DAL", "GOA FORWARD PARTY", "MAHARASHTRAWADI GOMNTAK PARTY", "SIKKIM KRANTIKARI MORCHA", "JANASENA PARTY", "SIKKIM DEMOCRATIC FRONT"]
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
