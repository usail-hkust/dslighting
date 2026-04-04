# plot-line-021

Draw a line chart depicting the electricity consumption of various Southeast Asian countries over time, based on the format given in plot.yaml. Highlight the total electricity consumption for each country and create the chart according to the required output format

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
# Description

> Uncover this dataset showcasing sustainable energy indicators and other useful factors across all countries from 2000 to 2020. Dive into vital aspects such as electricity access, renewable energy, carbon emissions, energy intensity, Financial flows, and economic growth. Compare nations, track progress towards Sustainable Development Goal 7, and gain profound insights into** ****global energy consumption patterns** over time.** **

# Key Features:

> * **Entity** : The name of the country or region for which the data is reported.
> * **Year** : The year for which the data is reported, ranging from 2000 to 2020.
> * **Access to electricity (% of population)** : The percentage of population with access to electricity.
> * **Access to clean fuels for cooking (% of population)** : The percentage of the population with primary reliance on clean fuels.
> * **Renewable-electricity-generating-capacity-per-capita** : Installed Renewable energy capacity per person
> * **Financial flows to developing countries (US $)** : Aid and assistance from developed countries for clean energy projects.
> * **Renewable energy share in total final energy consumption (%)** : Percentage of renewable energy in final energy consumption.
> * **Electricity from fossil fuels (TWh)** : Electricity generated from fossil fuels (coal, oil, gas) in terawatt-hours.
> * **Electricity from nuclear (TWh)** : Electricity generated from nuclear power in terawatt-hours.
> * **Electricity from renewables (TWh)** : Electricity generated from renewable sources (hydro, solar, wind, etc.) in terawatt-hours.
> * **Low-carbon electricity (% electricity)** : Percentage of electricity from low-carbon sources (nuclear and renewables).
> * **Primary energy consumption per capita (kWh/person)** : Energy consumption per person in kilowatt-hours.
> * **Energy intensity level of primary energy (MJ/$2011 PPP GDP)** : Energy use per unit of GDP at purchasing power parity.
> * **Value_co2_emissions (metric tons per capita)** : Carbon dioxide emissions per person in metric tons.
> * **Renewables (% equivalent primary energy)** : Equivalent primary energy that is derived from renewable sources.
> * **GDP growth (annual %)** : Annual GDP growth rate based on constant local currency.
> * **GDP per capita** : Gross domestic product per person.
> * **Density (P/Km2)** : Population density in persons per square kilometer.
> * **Land Area (Km2)** : Total land area in square kilometers.
> * **Latitude** : Latitude of the country's centroid in decimal degrees.
> * **Longitude** : Longitude of the country's centroid in decimal degrees.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
figsize: [10.0, 6.0]
graph_title: "Electricity Consumption in SEA : Total Electricity"
labels: ["Cambodia", "Indonesia", "Malaysia", "Myanmar", "Philippines", "Singapore", "Thailand"]
x_label: "Year"
y_label: "Total Electricity"
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
