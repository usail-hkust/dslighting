# plot-scatter-012

Complete missing data with mean interpolation, then explore how population density correlates with GDP. Produce a scatter plot formatted according to plot.yaml guidelines and

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
# Description

> This comprehensive dataset provides a wealth of information about** ** **all countries worldwide** , covering a wide range of indicators and attributes. It encompasses demographic statistics, economic indicators, environmental factors, healthcare metrics, education statistics, and much more. With every country represented, this dataset offers a complete global perspective on various aspects of nations, enabling in-depth analyses and cross-country comparisons.

# Key Features

> * **Country** : Name of the country.
> * **Density (P/Km2)** : Population density measured in persons per square kilometer.
> * **Abbreviation** : Abbreviation or code representing the country.
> * **Agricultural Land (%)** : Percentage of land area used for agricultural purposes.
> * **Land Area (Km2)** : Total land area of the country in square kilometers.
> * **Armed Forces Size** : Size of the armed forces in the country.
> * **Birth Rate** : Number of births per 1,000 population per year.
> * **Calling Code** : International calling code for the country.
> * **Capital/Major City** : Name of the capital or major city.
> * **CO2 Emissions** : Carbon dioxide emissions in tons.
> * **CPI** : Consumer Price Index, a measure of inflation and purchasing power.
> * **CPI Change (%)** : Percentage change in the Consumer Price Index compared to the previous year.
> * **Currency_Code** : Currency code used in the country.
> * **Fertility Rate** : Average number of children born to a woman during her lifetime.
> * **Forested Area (%)** : Percentage of land area covered by forests.
> * **Gasoline_Price** : Price of gasoline per liter in local currency.
> * **GDP** : Gross Domestic Product, the total value of goods and services produced in the country.
> * **Gross Primary Education Enrollment (%)** : Gross enrollment ratio for primary education.
> * **Gross Tertiary Education Enrollment (%)** : Gross enrollment ratio for tertiary education.
> * **Infant Mortality** : Number of deaths per 1,000 live births before reaching one year of age.
> * **Largest City** : Name of the country's largest city.
> * **Life Expectancy** : Average number of years a newborn is expected to live.
> * **Maternal Mortality Ratio** : Number of maternal deaths per 100,000 live births.
> * **Minimum Wage** : Minimum wage level in local currency.
> * **Official Language** : Official language(s) spoken in the country.
> * **Out of Pocket Health Expenditure (%)** : Percentage of total health expenditure paid out-of-pocket by individuals.
> * **Physicians per Thousand** : Number of physicians per thousand people.
> * **Population** : Total population of the country.
> * **Population: Labor Force Participation (%)** : Percentage of the population that is part of the labor force.
> * **Tax Revenue (%)** : Tax revenue as a percentage of GDP.
> * **Total Tax Rate** : Overall tax burden as a percentage of commercial profits.
> * **Unemployment Rate** : Percentage of the labor force that is unemployed.
> * **Urban Population** : Percentage of the population living in urban areas.
> * **Latitude** : Latitude coordinate of the country's location.
> * **Longitude** : Longitude coordinate of the country's location.
>

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#1f77b4"]
figsize: [10.0, 6.0]
graph_title: "Population Density vs. GDP"
x_label: "GDP"
y_label: "Density (P/Km2)"
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
