# plot-bar-008

Calculate the gender distribution by country, create a bar chart to visualize the results, and . Please refer to 'plot_details.txt' for additional specifications

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

Welcome to Kaggle's second annual Machine Learning and Data Science Survey ― and our first-ever survey data challenge.

This year,** **[as last year](https://www.kaggle.com/kaggle/kaggle-survey-2017), we set out to conduct an industry-wide survey that presents a truly comprehensive view of the state of data science and machine learning. The survey was live for one week in October, and after cleaning the data we finished with 23,859 responses, a 49% increase over last year!

There's a lot to explore here. The results include raw numbers about who is working with data, what’s happening with machine learning in different industries, and the best ways for new data scientists to break into the field. We've published the data in as raw a format as possible without compromising anonymization, which makes it an unusual example of a survey dataset.

---

# Challenge

This year Kaggle is launching the first Data Science Survey Challenge, where we will be awarding a prize pool of $28,000 to kernel authors who tell a rich story about a subset of the data science and machine learning community..** **

In our second year running this survey, we were once again awed by the global, diverse, and dynamic nature of the data science and machine learning industry. This** **[survey data EDA](https://www.kaggle.com/paultimothymooney/2018-kaggle-ml-and-ds-survey-eda) provides an overview of the industry on an aggregate scale, but it also leaves us wanting to know more about the many specific communities comprised within the survey. For that reason, we’re inviting the Kaggle community to dive deep into the survey datasets and help us tell the diverse stories of data scientists from around the world.** **

**The challenge objective:** tell a data story about a subset of the data science community represented in this survey, through a combination of both narrative text and data exploration. A “story” could be defined any number of ways, and that’s deliberate. The challenge is to deeply explore (through data) the impact, priorities, or concerns of a specific group of data science and machine learning practitioners. That group can be defined in the macro (for example: anyone who does most of their coding in Python) or the micro (for example: female data science students studying machine learning in masters programs). This is an opportunity to be creative and tell the story of a community you identify with or are passionate about!** **

Submissions will be evaluated on the following:** **

* Composition - Is there a clear narrative thread to the story that’s articulated and supported by data? The subject should be well defined, well researched, and well supported through the use of data and visualizations.** **
* Originality - Does the reader learn something new through this submission? Or is the reader challenged to think about something in a new way? A great entry will be informative, thought provoking, and fresh all at the same time.** **
* Documentation - Are your code, and kernel, and additional data sources well documented so a reader can understand what you did? Are your sources clearly cited? A high quality analysis should be concise and clear at each step so the rationale is easy to follow and the process is reproducible** **

To be valid, a submission must be contained in one kernel, made public on or before the submission deadline. Participants are free to use any datasets in addition to the Kaggle Data Science survey, but those datasets must also be publicly available on Kaggle by the deadline for a submission to be valid.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
type: "bar"
color: ["#2ca02c", "#ff7f0e", "#1f77b4"]
figsize: [16.0, 8.0]
graph_title: "Country-wise gender distribution"
labels: ["Female", "Male", "Others"]
x_label: "Country"
y_label: "Percentage"
xtick_labels: ["Brazil", "Canada", "China", "France", "Germany", "India", "Japan", "Russia", "UK & Northern Ireland", "USA"]
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
