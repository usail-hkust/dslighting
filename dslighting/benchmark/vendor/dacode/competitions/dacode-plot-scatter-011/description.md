# plot-scatter-011

Examine how streams relate to the number of times the most popular songs of 2023 are added to Spotify playlists. Clean the dataset by removing unnecessary columns, handling duplicates, and converting relevant columns to numeric. Generate a scatter plot as per the specifications outlined in plot.yaml, and create the chart according to the required output format

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
# Description :

> This dataset contains a comprehensive list of the most famous songs of 2023 as listed on Spotify. The dataset offers a wealth of features beyond what is typically available in similar datasets. It provides insights into each song's attributes, popularity, and presence on various music platforms. The dataset includes information such as** ** **track name, artist(s) name, release date, Spotify playlists and charts, streaming statistics, Apple Music presence, Deezer presence, Shazam charts, and various audio features** .

# Key Features:

> * **track_name** :** ***Name of the song*
> * **artist(s)_name** :** ***Name of the artist(s) of the song*
> * **artist_count** :** ***Number of artists contributing to the song*
> * **released_year** :** ***Year when the song was released*
> * **released_month** :** ***Month when the song was released*
> * **released_day** :** ***Day of the month when the song was released*
> * **in_spotify_playlists** :** ***Number of Spotify playlists the song is included in*
> * **in_spotify_charts** :** ***Presence and rank of the song on Spotify charts*
> * **streams** :** ***Total number of streams on Spotify*
> * **in_apple_playlists** :** ***Number of Apple Music playlists the song is included in*
> * **in_apple_charts** :** ***Presence and rank of the song on Apple Music charts*
> * **in_deezer_playlists** :** ***Number of Deezer playlists the song is included in*
> * **in_deezer_charts** :** ***Presence and rank of the song on Deezer charts*
> * **in_shazam_charts** :** ***Presence and rank of the song on Shazam charts*
> * **bpm** :** ***Beats per minute, a measure of song tempo*
> * **key** :** ***Key of the song*
> * **mode** :** ***Mode of the song (major or minor)*
> * **danceability_%** :** ***Percentage indicating how suitable the song is for dancing*
> * **valence_%** :** ***Positivity of the song's musical content*
> * **energy_%** :** ***Perceived energy level of the song*
> * **acousticness_%** :** ***Amount of acoustic sound in the song*
> * **instrumentalness_%** :** ***Amount of instrumental content in the song*
> * **liveness_%** :** ***Presence of live performance elements*
> * **speechiness_%** :** ***Amount of spoken words in the song*
>

---

## Chart Format Specification

The following formatting requirements are specified in `plot.yaml` (the file is available in your workspace):

```yaml
color: ["#1f77b4"]
figsize: [10.0, 6.0]
graph_title: "Relationship Between Most Streamed Songs And Spotify Playlists In 2023"
x_label: "Streams"
y_label: "Number of Spotify Playlists"
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
