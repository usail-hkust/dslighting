# plot-bar-003

Identify the top ten authors with the highest average book prices. Sort them in **descending order** (highest average price first). Create a horizontal bar chart with dimensions of 18 by 12, label the y-axis as 'Author', the x-axis as 'Average Price', and the title as 'Most Expensive Author'.

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
This project is all about taking a closer look at the books available on Amazon. We've collected information on different types of genres, sub-genres, and individual books like their titles, authors, prices, and ratings. By digging into this data, we hope to learn interesting things about what kinds of books are popular, how they're priced, and what people like to read. This can help us understand more about the world of books and what makes them tick on Amazon.

### Dataset 1: Genre

* **Title** : This column contains the main genres of books available on Amazon.
* **Number of Sub-genres** : Indicates the count of sub-genres associated with each main genre.
* **URL** : Provides the link to the page on Amazon where books of this genre are listed.

### Dataset 2: SubGenre

* **Title** : Lists the specific sub-genres within each main genre.
* **Main Genre** : Indicates the overarching genre to which each sub-genre belongs.
* **No. of Books** : Shows the count of books categorized under each sub-genre.
* **URL** : Provides the link to the page on Amazon where books of this sub-genre are listed.

### Dataset 3: Books_df

* **Title** : The title of the book.
* **Author** : Name of the author or publication house.
* **Main Genre** : The main genre the book belongs to.
* **Sub Genre** : The specific sub-genre of the book.
* **Type** : Indicates the format of the book, such as paperback, Kindle, audiobook, or hardcover.
* **Price** : The price of the book.
* **Rating** : The average rating of the book given by users.
* **No. of People Rated** : Indicates the count of users who have rated the book.
* **URLs** : Provides the link to the book's page on Amazon for further details and purchase options.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
type: "bar"
color: ["#dfab20", "#df9920", "#df5420", "#dfbd20", "#df7720", "#df3120", "#dfce20", "#df4220", "#df6620", "#df8820"]
figsize: [18.0, 12.0]
graph_title: "Most Expensive Author"
x_label: "Average Price"
y_label: "Author"
xtick_labels: ["0", "5000", "10000", "15000", "20000", "25000", "30000", "35000", "40000"]
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
