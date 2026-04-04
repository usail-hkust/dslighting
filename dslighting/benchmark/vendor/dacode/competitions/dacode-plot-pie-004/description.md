# plot-pie-004

Use the Student Alcohol Consumption dataset to create a pie chart showing the distribution of final grades (G3) for students with weekly alcohol consumption levels (2 to 10). Combine weekday and weekend alcohol consumption into a single value. Use the colors ‘lime’, ‘blue’, ‘orange’, ‘cyan’, ‘grey’, ‘purple’, ‘brown’, ‘red’, and ‘darksalmon’.

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
## Context:

The data were obtained in a survey of students math and portuguese language courses in secondary school. It contains a lot of interesting social, gender and study information about students. You can use it for some EDA or try to predict students final grade.

## Content:

Attributes for both student-mat.csv (Math course) and student-por.csv (Portuguese language course) datasets:** **

1. school - student's school (binary: 'GP' - Gabriel Pereira or 'MS' - Mousinho da Silveira)
2. sex - student's sex (binary: 'F' - female or 'M' - male)** **
3. age - student's age (numeric: from 15 to 22)** **
4. address - student's home address type (binary: 'U' - urban or 'R' - rural)** **
5. famsize - family size (binary: 'LE3' - less or equal to 3 or 'GT3' - greater than 3)** **
6. Pstatus - parent's cohabitation status (binary: 'T' - living together or 'A' - apart)
7. Medu - mother's education (numeric: 0 - none, 1 - primary education (4th grade), 2 – 5th to 9th grade, 3 – secondary education or 4 – higher education)
8. Fedu - father's education (numeric: 0 - none, 1 - primary education (4th grade), 2 – 5th to 9th grade, 3 – secondary education or 4 – higher education)
9. Mjob - mother's job (nominal: 'teacher', 'health' care related, civil 'services' (e.g. administrative or police), 'at_home' or 'other')** **
10. Fjob - father's job (nominal: 'teacher', 'health' care related, civil 'services' (e.g. administrative or police), 'at_home' or 'other')** **
11. reason - reason to choose this school (nominal: close to 'home', school 'reputation', 'course' preference or 'other')** **
12. guardian - student's guardian (nominal: 'mother', 'father' or 'other')** **
13. traveltime - home to school travel time (numeric: 1 - <15 min., 2 - 15 to 30 min., 3 - 30 min. to 1 hour, or 4 - >1 hour)** **
14. studytime - weekly study time (numeric: 1 - <2 hours, 2 - 2 to 5 hours, 3 - 5 to 10 hours, or 4 - >10 hours)** **
15. failures - number of past class failures (numeric: n if 1<=n<3, else 4)** **
16. schoolsup - extra educational support (binary: yes or no)** **
17. famsup - family educational support (binary: yes or no)** **
18. paid - extra paid classes within the course subject (Math or Portuguese) (binary: yes or no)** **
19. activities - extra-curricular activities (binary: yes or no)** **
20. nursery - attended nursery school (binary: yes or no)** **
21. higher - wants to take higher education (binary: yes or no)** **
22. internet - Internet access at home (binary: yes or no)** **
23. romantic - with a romantic relationship (binary: yes or no)** **
24. famrel - quality of family relationships (numeric: from 1 - very bad to 5 - excellent)** **
25. freetime - free time after school (numeric: from 1 - very low to 5 - very high)** **
26. goout - going out with friends (numeric: from 1 - very low to 5 - very high)** **
27. Dalc - workday alcohol consumption (numeric: from 1 - very low to 5 - very high)** **
28. Walc - weekend alcohol consumption (numeric: from 1 - very low to 5 - very high)** **
29. health - current health status (numeric: from 1 - very bad to 5 - very good)** **
30. absences - number of school absences (numeric: from 0 to 93)** **

These grades are related with the course subject, Math or Portuguese:** **

1. G1 - first period grade (numeric: from 0 to 20)** **
2. G2 - second period grade (numeric: from 0 to 20)** **
3. G3 - final grade (numeric: from 0 to 20, output target)** **

**Additional note:** there are several (382) students that belong to both datasets .** **
These students can be identified by searching for identical attributes
that characterize each student, as shown in the annexed R file.

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
type: "pie"
color: ["#00ff00", "#e9967a", "#00ffff", "#ffa500", "#a52a2a", "#808080", "#ff0000", "#0000ff", "#800080"]
figsize: [6.4, 4.8]
graph_title: "Final Grade"
x_label: "Students grade distribution according to weekly alcohol consumption"
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
