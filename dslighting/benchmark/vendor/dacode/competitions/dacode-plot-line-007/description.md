# plot-line-007

Using the 17K Mobile Strategy Game dataset, plot the yearly average size (MB) of four major game genres from 2008 to 2019. Follow the instructions in guidance.txt and the formatting in plot.yaml

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
# Overview

The mobile games industry is worth billions of dollars, with companies spending vast amounts of money on the development and marketing of these games to an equally large market. Using this data set, insights can be gained into a sub-market of this market, strategy games. This sub-market includes titles such as Clash of Clans, Plants vs Zombies and Pokemon GO.

# Background

This is the data of 17007 strategy games on the Apple App Store. It was collected on the 3rd of August 2019, using the** **[iTunes API](https://affiliate.itunes.apple.com/resources/documentation/itunes-store-web-service-search-api) and the** **[App Store sitemap](https://apps.apple.com/us/genre/ios-games/id6014).** **

# Some ideas

You could use the number of ratings as a proxy indicator for the overall success of a game, and then work out what factors make a successful game. Or you could measure the state of the market over time and try predict where it is headed.
And I think an analysis of the icons of the apps would be pretty cool

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#1f77b4", "#2ca02c", "#d62728", "#ff7f0e"]
figsize: [16.0, 6.0]
graph_title: "Game size changes over 12 years by Genre"
labels: ["Action", "Puzzle", "Adventure", "Family"]
x_label: "Year"
y_label: "Game Size in MB"
xtick_labels: ["2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019"]
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
