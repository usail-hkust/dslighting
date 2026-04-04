# plot-pie-016

Analyze the distribution of coupon statuses in the dataset and create a pie chart according to the format specified in plot.yaml.

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
Dataset: Online Shopping Dataset;
CustomerID
Description: Unique identifier for each customer.
Data Type: Numeric;
Gender:
Description: Gender of the customer (e.g., Male, Female).
Data Type: Categorical;
Location:
Description: Location or address information of the customer.
Data Type: Text;
Tenure_Months:
Description: Number of months the customer has been associated with the platform.
Data Type: Numeric;
Transaction_ID:
Description: Unique identifier for each transaction.
Data Type: Numeric;
Transaction_Date:
Description: Date of the transaction.
Data Type: Date;
Product_SKU:
Description: Stock Keeping Unit (SKU) identifier for the product.
Data Type: Text;
Product_Description:
Description: Description of the product.
Data Type: Text;
Product_Category:
Description: Category to which the product belongs.
Data Type: Categorical;
Quantity:
Description: Quantity of the product purchased in the transaction.
Data Type: Numeric;
Avg_Price:
Description: Average price of the product.
Data Type: Numeric;
Delivery_Charges:
Description: Charges associated with the delivery of the product.
Data Type: Numeric;
Coupon_Status:
Description: Status of the coupon associated with the transaction.
Data Type: Categorical;
GST:
Description: Goods and Services Tax associated with the transaction.
Data Type: Numeric;
Date:
Description: Date of the transaction (potentially redundant with Transaction_Date).
Data Type: Date;
Offline_Spend:
Description: Amount spent offline by the customer.
Data Type: Numeric;
Online_Spend:
Description: Amount spent online by the customer.
Data Type: Numeric;
Month:
Description: Month of the transaction.
Data Type: Categorical;
Coupon_Code:
Description: Code associated with a coupon, if applicable.
Data Type: Text;
Discount_pct:
Description: Percentage of discount applied to the transaction.
Data Type: Numeric;

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#2ca02c", "#ff7f0e", "#1f77b4"]
figsize: [10.0, 6.0]
labels: ["Clicked", "Used", "Not Used"]
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
