# plot-scatter-006

Complete the given analysis.py to draw a scatter plot of book price versus rating. Ensure that the Price column is cleaned by removing currency symbols and converted to numeric. For better visualization, plot the log of the price on the x-axis. ’, with the image size set to (12, 8), the scatter plot color set to blue, the title as “Price vs. Rating of Books”, the x-axis labeled as “Log of Price”, and the y-axis labeled as “Rating”

## Output Requirements

You must create a **submission directory** containing exactly three files:

- rendered plot image artifact
- structured plot metadata JSON artifact
- numeric payload artifact extracted from the figure

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
* **URLs** : Provides the link to the book's page on Amazon for further details and purchase options

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
type: "scatter"
color: ["#1f77b4"]
figsize: [12.0, 8.0]
graph_title: "Price vs. Rating of Books"
x_label: "Price"
y_label: "Rating"
xtick_labels: ["$\mathdefault{10^{-4}}$", "$\mathdefault{10^{-3}}$", "$\mathdefault{10^{-2}}$", "$\mathdefault{10^{-1}}$", "$\mathdefault{10^{0}}$", "$\mathdefault{10^{1}}$", "$\mathdefault{10^{2}}$", "$\mathdefault{10^{3}}$", "$\mathdefault{10^{4}}$", "$\mathdefault{10^{5}}$", "$\mathdefault{10^{6}}$"]
ytick_labels: ["−1", "0", "1", "2", "3", "4", "5", "6"]
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

For scatter plots, save the **x and y coordinate pairs** as a **2D array with shape `(N, 2)`**, where N = number of scatter points:

```python
# x_values: sequential indices (0, 1, 2, ..., N-1) — the scatter point positions on x-axis
# y_values: the corresponding y-axis values (e.g., IMDb scores)
data_values = np.column_stack([x_values, y_values])  # shape: (N, 2)
np.save("<numeric_payload_artifact_path>", data_values)
```
