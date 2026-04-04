# plot-pie-008

Please find out which hub city has the largest biker average delivery distance. Then, generate a pie chart illustrating the distribution of order deliveries by driver modes in that city, adhering to the guidelines in 'plot.yaml'

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
## Delivery Center Overview

Delivery Center, with its various operational hubs across Brazil, integrates retailers and marketplaces, creating a healthy ecosystem for selling goods and food in the Brazilian retail market. The platform manages a catalog of over 900,000 items, with thousands of orders and deliveries processed daily through a network of retailers and delivery partners nationwide.

This generates a vast amount of data constantly. The business is increasingly data-driven, using data to make decisions and envisioning the intelligent use of data as a key market differentiator. This context presents a challenge to apply technical knowledge to solve everyday problems faced by a data team.

### Dataset Descriptions

* **channels:** Contains information about sales channels (marketplaces) where goods and food from retailers are sold.
* **deliveries:** Contains information about deliveries made by partner delivery personnel.
* **drivers:** Contains information about partner delivery personnel. They are based at hubs and handle deliveries to consumers' homes.
* **hubs:** Contains information about Delivery Center hubs, which are distribution centers for orders.
* **orders:** Contains information about sales processed through the Delivery Center platform.
* **payments:** Contains information about payments made to the Delivery Center.
* **stores:** Contains information about retailers using the Delivery Center platform to sell their items (goods and/or food) in marketplaces.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#ffdb00", "#ffb600"]
figsize: [8.0, 8.0]
graph_title: "Percentage of orders delivered by type of driver in CURITIBA"
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
