# Climate Science - Pattern Discovery

## Task Metadata

- Family: cyclone
- Local Task ID: 14
- Problem Type: Pattern Discovery
- Modality: timeseries, hdf (matrix), tabular

## Background

Identifying stable cyclone cloud structure patterns (e.g., D-structure, spiral bands) via unsupervised clustering (K-Means) using extracted cloud structure features (morphological, texture) from all cyclone satellite images in the AU dataset is critical for meteorology. Stable cloud structure patterns support standardized cyclone classification, which improves the understanding of cyclone evolution mechanisms and enhances intensity prediction accuracy.

## Task

Unsupervised clustering algorithms (e.g., K-Means) can stably cluster at least two distinct cloud structure patterns (e.g., D-structure, spiral bands) after extracting cloud structure features (morphological, texture) from all cyclone satellite images in the AU dataset.

## Raw Answer Target

Determine if the statement 'Unsupervised clustering algorithms (e.g., K-Means) can stably cluster at least two distinct cloud structure patterns from AU dataset cyclone satellite images' is true or false. Format your answer as: answer: {true} or answer: {false}.

## Domain Knowledge

Morphological features (eccentricity, solidity) reflect cloud shape; texture features (contrast, homogeneity) capture gray distribution regularity. K-Means groups data by feature similarity. Silhouette Score (>0.5 = good separation) and Calinski-Harabasz Score (higher = better compactness) assess clustering quality. PCA reduces dimensionality for visualizing cluster distinctness.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `14`.
Put only the final answer value inside `@answer[...]`.
Do not submit the full sentence unless the answer itself is a full sentence.
The grader will strip common prefixes such as `answer:` automatically.

Examples:
- numeric: `@answer[7.4]`
- boolean: `@answer[true]`
- string: `@answer[Temperature]`
- structured text: `@answer[[(3, -78)]]`

## Dataset Description
**Domain:** Earth Science
**Modalities:** timeseries, hdf (matrix), tabular

A comprehensive dataset for tropical cyclone (TC) research, integrating long-term satellite imagery, spatiotemporal metadata, and best-track data to support machine learning tasks such as intensity forecasting. It includes data from Southern Hemisphere (Around Australia, AU).

### Files

#### `metadata_2020_to_2024.csv`
A Digital Typhoon Dataset focusing on tropical cyclones in the Southern Hemisphere (around Australia, AU) from 2020 to 2024. It combines tabular metadata (e.g., position, intensity, timing) with HDF5-stored satellite brightness temperature matrices, processed using azimuthal equidistant projection. The dataset follows AU's TC season definition (July of the previous year to June) and uses BoM (Bureau of Meteorology, Australia) best-track data standardized to JMA (Japan Meteorological Agency) metrics (e.g., wind speed converted from m/s to kt).

| Column | Description |
|---|---|
| `year` | Calendar year of the tropical cyclone observation, formatted as a 4-digit integer (e.g., 2020) |
| `month` | Month of observation (1-12), aligned with AU's TC season (July-June, e.g., July 2023 is part of the 2023-2024 season) |
| `day` | Day of the month for the observation (1-31), representing the specific date of the satellite measurement |
| `hour` | Hour of the day for the observation (0-23), in UTC, indicating the exact time of the satellite image capture |
| `grade` | Tropical cyclone intensity grade (2-5 for tropical cyclones, 6 for extra-tropical storms), assigned using JMA's maximum wind speed thresholds applied to BoM best-track data |
| `lat` | Latitude of the tropical cyclone center (in degrees, negative values for Southern Hemisphere), derived from BoM best-track data, representing the spatial position of the cyclone |
| `lng` | Longitude of the tropical cyclone center (in degrees), derived from BoM best-track data, defining the east-west spatial position of the cyclone |
| `pressure` | Central pressure of the tropical cyclone (in hectopascals, hPa), with missing values filled via linear interpolation between BoM ground truth measurements; treated as ground truth for machine learning tasks |
| `wind` | Maximum sustained wind speed of the tropical cyclone (in knots, kt), converted from BoM's original m/s using the formula kt = m/s / 0.5144; missing values filled via persistence method (last known value) |
| `intp` | Binary indicator (0 or 1) for interpolated metadata: 1 if 'pressure' or 'wind' values are interpolated (78.8% of the full dataset), 0 if values are direct BoM ground truth measurements |
| `mask_pct` | Percentage of masked (corrupted or missing) pixels in the corresponding HDF5 brightness temperature matrix, due to sensor issues (common in older satellites like Himawari-3/4/5) affecting data quality |
| `id` | Unique identifier for each tropical cyclone (e.g., 202002), enabling tracking of individual cyclone life cycles across multiple observations |
| `hdf_full_path` | File path to the HDF5 file storing the 512×512 brightness temperature matrix (in Kelvin) from satellites; matrix uses azimuthal equidistant projection centered on the cyclone center |

#### `image_2020_to_2024`
HDF5-formatted files storing 512×512 spatial matrices of satellite brightness temperatures (a key metric for cyclone cloud structure analysis) for the AU subset (2020-2024). Each matrix corresponds to a single observation in the tabular metadata, processed with azimuthal equidistant projection to preserve distance from the cyclone center (critical for eye diameter measurement and center estimation tasks).
