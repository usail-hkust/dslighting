# plot-scatter-002

Create a stacked horizontal bar chart, which illustrates the average days per order stage forthe top 10 cities by sales. with settings from "plot.yaml"

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

# Data Science Jobs Salaries Dataset

## About Dataset
### Overview

This dataset comprises job postings and salary information related to data science roles in California, USA, sourced from SimplyHired. The dataset was scraped on 17 December 2021 and includes four CSV files. These files provide insights into job titles, companies, locations, salaries, qualifications, and benefits associated with data science positions.

### Contents

#### work_year

The year during which the salary was paid, categorized as either a specific year (e.g., 2020) or estimated (e.g., 2021e).

#### experience_level

The experience level of the job, classified as EN (Entry-level / Junior), MI (Mid-level / Intermediate), SE (Senior-level / Expert), or EX (Executive-level / Director).

#### employment_type

The type of employment for the role: PT (Part-time), FT (Full-time), CT (Contract), or FL (Freelance).

#### job_title

The specific role held during the year.

#### salary

The total gross salary amount paid.

#### salary_currency

The currency of the salary, represented as an ISO 4217 currency code.

#### salary_in_usd

The salary converted to USD, calculated using FX rates from fxdata.foorilla.com.

#### employee_residence

The primary country of residence of the employee during the work year, specified as an ISO 3166 country code.

#### remote_ratio

The percentage of work conducted remotely, categorized as 0 (No remote work), 50 (Partially remote), or 100 (Fully remote).

#### company_location

The country where the employer's main office or contracting branch is located, indicated by an ISO 3166 country code.

#### company_size

The average number of employees at the company during the year, categorized as S (less than 50 employees), M (50 to 250 employees), or L (more than 250 employees).

### Source and Acknowledgements

The dataset was obtained from SimplyHired and processed for analysis. The cleaning and scraping scripts used are available on GitHub for reference.

### Potential Uses

This dataset is valuable for tasks such as data cleaning exercises, exploratory data analysis, and building predictive models related to data science job trends and salaries in California.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
labels: ["home victory", "draw", "away victory"]
x_label: "estimated prob"
y_label: "observed prob"
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
