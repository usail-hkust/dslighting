# plot-line-014

Please use the 2017 stock return data for the 9 largest companies to calculate the daily cumulative returns for three portfolio strategies: equal-weight, market value-weighted, highest Sharpe ratio, and global minimum volatility. Generate a line plot as specified in 'plot.yaml' and . You can refer to 'analysis.py' for relevant code

## Output Requirements

Your final output must be a submission directory.

The exact directory name will be provided at runtime in the CRITICAL I/O REQUIREMENTS section.

Inside that directory, you must create exactly these three files:

- rendered plot image artifact
- structured plot metadata JSON artifact
- numeric payload artifact extracted from the figure

---

## Dataset Background

## Model Portfolio Overview

### Portfolio Construction

The model portfolio is constructed with pre-defined weights for some of the largest companies in the world just before January 2017. The table below lists the companies, their ticker symbols, and their respective portfolio weights:

| Company Name      | Ticker | Portfolio Weight |
| :---------------- | :----- | :--------------- |
| Apple             | AAPL   | 12%              |
| Microsoft         | MSFT   | 15%              |
| Exxon Mobil       | XOM    | 8%               |
| Johnson & Johnson | JNJ    | 5%               |
| JP Morgan         | JPM    | 9%               |
| Amazon            | AMZN   | 10%              |
| General Electric  | GE     | 11%              |
| Facebook          | FB     | 14%              |
| AT&T              | T      | 16%              |

### Market Capitalization

The table below shows the market capitalizations of the companies in the portfolio just before January 2017:

| Company Name      | Ticker | Market Cap ($ Billions) |
| ----------------- | ------ | ----------------------- |
| Apple             | AAPL   | 601.51                  |
| Microsoft         | MSFT   | 469.25                  |
| Exxon Mobil       | XOM    | 349.5                   |
| Johnson & Johnson | JNJ    | 310.48                  |
| JP Morgan         | JPM    | 299.77                  |
| Amazon            | AMZN   | 356.94                  |
| General Electric  | GE     | 268.88                  |
| Facebook          | FB     | 331.57                  |
| AT&T              | T      | 246.09                  |

### Sharpe Ratio

The Sharpe ratio, pioneered by William F. Sharpe, is a metric of risk-adjusted return. It is useful for determining how much risk is being taken to achieve a certain level of return. The formula for the Sharpe ratio is:

$$
S=\frac{R_a-r_f}{\sigma_a}
$$

Where:

- \( S \) = Sharpe Ratio
- \( R_a \) = Asset return
- \( r_f \) = Risk-free rate of return
- \( \sigma_a \) = Asset volatility

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
figsize: [12, 6]
graph_title: "Cumulative Returns Over Time"
labels:
  - "Cumulative EW"
  - "Cumulative MCap"
  - "Cumulative MSR"
  - "Cumulative GMV"
x_label: "Date"
y_label: "Cumulative Returns"
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
