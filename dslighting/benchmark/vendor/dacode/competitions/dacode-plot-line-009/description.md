# plot-line-009

Using the Daily Temperature of Major Cities dataset, plot the yearly average temperatures (in Celsius) for Karachi and Islamabad from 1995 to 2019. Follow the instructions in tips.txt and adhere to the formatting guidelines in plot.yaml.

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
Global warming is the ongoing rise of the average temperature of the Earth's climate system and has been demonstrated by direct temperature measurements and by measurements of various effects of the warming - Wikipedia

So a dataset on the temperature of major cities of the world will help analyze the same. Also weather information is helpful for a lot of data science tasks like sales forecasting, logistics etc.** **

Thanks to University of Dayton, the dataset is available as separate txt files for each city** **[here](http://academic.udayton.edu/kissock/http/Weather/default.htm). The data is available for research and non-commercial purposes only.. Please refer to** **[this page](http://academic.udayton.edu/kissock/http/Weather/default.htm)for license.

### Content
Daily level average temperature values is present in** **`city_temperature.csv` file

### Acknowledgements
University of Dayton for making this dataset available in the first place!

Photo credits:** **[James Day](https://unsplash.com/@jamesday?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on Unsplash

### Inspiration

Some ideas are:

1. How is the average temperature of the world changing over time?
2. Is the temperature information helpful for other forecasting tasks?

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#ff0000", "#008000"]
figsize: [12.0, 8.0]
graph_title: "Average Temperature Comparison between Karachi and Islamabad"
labels: ["Karachi", "Islamabad"]
x_label: "Year"
y_label: "AvgTemperature"
xtick_labels: ["1992", "1996", "2000", "2004", "2008", "2012", "2016", "2020", "2024"]
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
