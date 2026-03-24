# plot-scatter-013

Examine how job categories are distributed across different years of experience. Clean the dataset by grouping the job categories and calculating the frequency of each category by year. Convert job categories to numerical values for plotting. Create a scatter plot following plot.yaml guidelines to visualize this relationship, and save it as ‘result.png’

## Output Requirements

You must create a **submission directory** containing exactly three files:

- `result.png` - The final rendered plot image
- `plot.json` - Structured plot metadata  
- `result.npy` - Numeric plot payload extracted from the figure

The exact directory name will be provided at runtime in the CRITICAL I/O REQUIREMENTS section.

Inside that directory, you must create exactly these three files:

- `result.png` - the final rendered plot image
- `plot.json` - structured plot metadata
- `result.npy` - numeric plot payload extracted from the figure

---

## Dataset Background

## About Dataset

 **work_year** : The year in which the data was recorded. This field indicates the temporal context of the data, important for understanding salary trends over time.

 **job_title** : The specific title of the job role, like 'Data Scientist', 'Data Engineer', or 'Data Analyst'. This column is crucial for understanding the salary distribution across various specialized roles within the data field.

 **job_category** : A classification of the job role into broader categories for easier analysis. This might include areas like 'Data Analysis', 'Machine Learning', 'Data Engineering', etc.

 **salary_currency** : The currency in which the salary is paid, such as USD, EUR, etc. This is important for currency conversion and understanding the actual value of the salary in a global context.

 **salary** : The annual gross salary of the role in the local currency. This raw salary figure is key for direct regional salary comparisons.

 **salary_in_usd** : The annual gross salary converted to United States Dollars (USD). This uniform currency conversion aids in global salary comparisons and analyses.

 **employee_residence** : The country of residence of the employee. This data point can be used to explore geographical salary differences and cost-of-living variations.

 **experience_level** : Classifies the professional experience level of the employee. Common categories might include 'Entry-level', 'Mid-level', 'Senior', and 'Executive', providing insight into how experience influences salary in data-related roles.

 **employment_type** : Specifies the type of employment, such as 'Full-time', 'Part-time', 'Contract', etc. This helps in analyzing how different employment arrangements affect salary structures.

 **work_setting** : The work setting or environment, like 'Remote', 'In-person', or 'Hybrid'. This column reflects the impact of work settings on salary levels in the data industry.

 **company_location** : The country where the company is located. It helps in analyzing how the location of the company affects salary structures.

 **company_size** : The size of the employer company, often categorized into small (S), medium (M), and large (L) sizes. This allows for analysis of how company size influences salary.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
figsize: [16.0, 8.0]
graph_title: "Job Category Distribution by Work Year"
x_label: "Work Year"
y_label: "Job Category"
ytick_labels: ["Data Analysis", "Data Engineering", "Data Science and Research", "Machine Learning and AI", "Data Architecture and Modeling", "Data Management and Strategy", "Leadership and Management", "BI and Visualization", "Cloud and Database", "Data Quality and Operations"]
```

Your chart output **must** match these values exactly.

---

## Output File Format Details

### `plot.json` — Required Keys

Your `plot.json` MUST use **exactly** these keys (the same schema as `sample_plot.json` in your workspace):

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
fig.savefig(f"{output_dir}/result.png")

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
with open(f"{output_dir}/plot.json", "w") as f:
    json.dump(plot_meta, f)
```

### `result.npy` — Required Shape

Save the **primary numeric data** of the plot (bar heights, line y-values, pie sizes, scatter y-values) as a **2D array with shape `(1, N)`**, where N = number of data points:

```python
np.save(f"{output_dir}/result.npy", data_values.reshape(1, -1))
```
