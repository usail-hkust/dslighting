# plot-bar-002

Draw a stacked bar chart that displays the percentage of restaurants offering online ordering options versus those not offering online ordering options across different rating levels. The title of the image should be "Percentage of Restaurants' Online Order Option by Rating", with the xlabel as "Rating", and the ylabel as "Percentage of Online Orders"

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
By analyzing this data, you can gain valuable insights that will help you in your decision-making process. Here are some types of analysis you can perform on Zomato data:

Geographical Analysis: You can see the locations of the branches in Bengaluru on a map.

Popular Dishes: You can use a word cloud to analyze the most ordered dishes of a particular restaurant.** **
For example; chicken paratha, pizza, biryani, burger masala, vada pav, paneer, and french fries.

Popular Cuisines: You can analyze the most preferred cuisines in Bengaluru. From this graph, you can see that North Indian cuisines are more popular in Bengaluru, despite it being a South Indian city.

Price-Rating Relationship: You can compare the relationship between price and rating for restaurants that accept online orders and those that do not. The orange data points represent restaurants that do not accept online orders.

Top Rated Restaurant: With the help of such graphs, you can find the restaurants with the highest ratings.

In this project, we will try to extract useful information from the data and create beautiful visualizations.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
type: "bar"
color: ["#ff7f0e", "#1f77b4"]
figsize: [6.4, 4.8]
graph_title: "Percentage of Restaurants' Online Order Option by Rating"
legend_title: "online_order"
labels: ["No", "Yes"]
x_label: "Rating"
y_label: "Percentage of Online Orders"
xtick_labels: ["1.8", "2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "4.0", "4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9"]
ytick_labels: ["0", "20", "40", "60", "80", "100", "120"]
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
