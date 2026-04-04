# plot-line-002

Using the Indian Premier League dataset, identify teams with more than 100 matches. Create a line graph showing the total runs scored in each over by these teams. Label the teams using abbreviations from teamabbreviations.md.

## Output Requirements

Your final output must be a submission directory.

The exact directory name will be provided at runtime in the CRITICAL I/O REQUIREMENTS section.

Inside that directory, you must create exactly these three files:

- rendered plot image artifact
- structured plot metadata JSON artifact
- numeric payload artifact extracted from the figure

---

## Dataset Background

About Dataset
Context

Cricket is a sport with a rich history and diverse culture, which has had a profound impact and garnered widespread appeal, making it one of the most prominent sporting events globally. The allure of cricket lies in its unique format and rules, attracting billions of fans worldwide. In cricket matches, teams take turns batting and fielding. Each team has the opportunity to showcase both their offensive and defensive capabilities, striving for victory with determination and grit.

In T20 international cricket matches, the relatively shorter duration and faster pace make it more suitable for the modern fast-paced lifestyle. Each game consists of 20 "overs," with each "over" comprising 6 balls. This high-intensity contest within a short timeframe not only tests players' technical skills and physical fitness but also provides continuous excitement and thrill for the spectators, igniting their passion and excitement.

Cricket matches are not just sporting competitions but also cultural and social events. Whether on or off the field, cricket carries rich cultural significance and social relevance. Fans gather together, cheering for their supported teams, sharing the highs and lows of the game, fostering unity and enthusiasm that serve as a bond among people.

Across the globe, cricket is beloved by people and has become an integral part of their lives. It represents not only sport and competition but also conveys the spirit of friendship, teamwork, and striving for excellence, serving as a common cultural symbol that tightly binds people together.

Content

All Indian Premier League Cricket matches between 2008 and 2016.

This is the ball by ball data of all the IPL cricket matches till season 9.

The dataset contains 2 files: deliveries.csv and matches.csv.

matches.csv contains details related to the match such as location, contesting teams, umpires, results, etc.

deliveries.csv is the ball-by-ball data of all the IPL matches including data of the batting team, batsman, bowler, non-striker, runs scored, etc

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
type: "line"
color: ["#bfbf00", "#6666ff", "#0000ff", "#a52a2a", "#ffb6b2", "#ff0000", "#008000"]
figsize: [6.4, 4.8]
legend_title: "batting_team"
labels: ["MI", "RCB", "KKR", "KXIP", "DD", "CSK", "RR"]
x_label: "over"
y_label: "total runs scored"
xtick_labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
ytick_labels: ["600", "700", "800", "900", "1000", "1100", "1200", "1300", "1400", "1500", "1600"]
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
