# Earth System Science - Correlational

## Task Metadata

- Family: terra
- Local Task ID: 5
- Problem Type: Correlational
- Modality: timeseries, tabular

## Background

Investigating the time series correlation between air temperature and shortwave radiation is critical for understanding the temporal dynamics of energy exchange in the Earth's atmosphere. Shortwave radiation (solar radiation) is a primary driver of short-term thermal variations, and quantifying the significance of their time series relationship aids in analyzing seasonal and interannual thermal responses to solar input.

## Task

The time series correlation between air temperature and shortwave radiation is statistically significant (i.e., p < 0.05), indicating a reliable linear association between their temporal variations.

## Raw Answer Target

Fill in the sentence: The p value of the time series correlation between air temperature and shortwave radiation is {p_value}.

## Domain Knowledge

Shortwave radiation (solar radiation) is a key temporal driver of air temperature variations, but their time series relationship can be obscured by seasonal cycles, cloud cover, and atmospheric circulation. Time series correlation analysis (Pearson's r) quantifies linear temporal associations, with statistical significance determined by p-values—p < 0.05 indicates a correlation unlikely to occur by random chance, while p ≥ 0.05 denotes a non-significant relationship.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `79`.
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
**Modalities:** timeseries, text, images

A multimodal spatio-temporal dataset spanning the Earth, encompassing daily and monthly timeseries data from 6,480,000 grid areas worldwide from 2021 to 2023, along with multimodal spatial supplementary information including geo-images and explanatory text, aiming to advance spatio-temporal data analysis and spatial intelligence research.

### Files

#### `timeseries`
A folder including various meteorological timeseries data in each 1degree * 1degree grid region across the globe (with a total of 360*180=64800 grids). Except for the first 'Date' column (already in standard format: YYYY-MM-DD) in every file, each column represent a 1degree * 1degree spatial unit, arranged in a z-shaped pattern from the lower-left corner (-90 latitude, -180 longitude) to the upper-right corner (90 latitude, 180 longitude), with the starting point being (-180, -90) and the endpoint being (180, 90). These column names have been rewritten into xxN/S_xxE/W for easier understanding.

| File | Description |
|---|---|
| `precipitation_monthly_1degree_2021_to_2023.csv` | Amount of precipitation (mm) monthly data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |
| `pres_monthly_1degree_2021_to_2023.csv` | Surface pressure (Pa) monthly data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |
| `relhumidity_monthly_1degree_2021_to_2023.csv` | Relative humidity (%) monthly data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |
| `spechumidity_monthly_1degree_2021_to_2023.csv` | Specific humidity (g/g) monthly data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |
| `swd_monthly_1degree_2021_to_2023.csv` | Downward shortwave radiation (W/m²) monthly data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |
| `lwd_monthly_1degree_2021_to_2023.csv` | Downward longwave radiation (W/m²) monthly data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |
| `temp_monthly_1degree_2021_to_2023.csv` | Air temperature (°C) monthly data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |
| `wind_monthly_1degree_2021_to_2023.csv` | Wind speed (m/s) monthly data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |
| `temp_daily_1degree_2021_to_2023.csv` | Air temperature (°C) daily data in each 1degree * 1degree spatial unit across the globe from 2021 to 2023. |

#### `metadata_merged.xlsx`
An excel file including textual metadata and descriptions for each 1degree * 1degree grid region across the globe (with a total of 360*180=64800 grids). Incorporation of these materials supplement spatio-temporal data analysis and enhance spatial intelligence research.

| Column | Description |
|---|---|
| `Latitude range` | The latitude interval of the grid area, for instance, in meta_0S_1W.txt the latitude range is (-1, 0). |
| `Longitude range` | The longitude interval of the grid area, for instance, in meta_0S_1W.txt the longitude range is (1, 0). |
| `Country` | The country that the grid area belongs to, could be None. |
| `Landvegetation (not a real column in the file, refer to description for details)` | The types and proportions of land vegetation in the grid area. It is possible to have more than one type of land vegetation in a single grid area. List of land vegetation types in this dataset: ['water', 'cropland_irrigated', 'snow_and_ice', 'grassland', 'sparse_vegetation', 'tree_needleleaved_deciduous_closed_to_open', 'shrubland', 'tree_broadleaved_deciduous_closed_to_open', 'tree_broadleaved_evergreen_closed_to_open', 'tree_broadleaved_deciduous_open', 'bare_areas', 'mosaic_cropland', 'tree_needleleaved_evergreen_closed_to_open', 'mosaic_tree_and_shrub', 'cropland_rainfed', 'cropland_rainfed_herbaceous_cover', 'tree_needleleaved_evergreen_closed', 'tree_broadleaved_deciduous_closed', 'shrubland_deciduous', 'tree_mixed', 'mosaic_herbaceous', 'tree_cover_flooded_fresh_or_brakish_water', 'lichens_and_mosses', 'shrubland_evergreen', 'urban', 'shrub_or_herbaceous_cover_flooded', 'mosaic_natural_vegetation', 'cropland_rainfed_tree_or_shrub_cover', 'sparse_herbaceous', 'tree_cover_flooded_saline_water', 'bare_areas_consolidated', 'sparse_shrub']. The values stored in these columns represent corresponding proportions of land vegetation within the grid area.  |
| `Climate (not a real column in the file, refer to description for details)` | The climate type of the grid area. It is possible to have more than one climate type in a single grid area. List of climate types in this dataset: ['dry_steppe_hot_arid', 'polar_frost', 'snow_fully_humid_warm_summer', 'mild_temperate_dry_summer_cool_summer', 'snow_dry_winter_cold_summer', 'tropical_dry_summer', 'dry_desert_cold_arid', 'polar_tundra', 'tropical_fully_humid', 'dry_desert_hot_arid', 'snow_fully_humid_cool_summer', 'tropical_dry_winter', 'mild_temperate_dry_winter_hot_summer', 'mild_temperate_fully_humid_hot_summer', 'mild_temperate_dry_summer_warm_summer', 'mild_temperate_fully_humid_warm_summer', 'snow_fully_humid_hot_summer', 'tropical_monsoon', 'mild_temperate_dry_summer_hot_summer', 'dry_steppe_cold_arid', 'snow_dry_winter_hot_summer', 'mild_temperate_fully_humid_cool_summer', 'snow_fully_humid_cold_summer', 'snow_dry_winter_warm_summer', 'mild_temperate_dry_winter_warm_summer', 'snow_dry_winter_cool_summer', 'snow_dry_summer_cool_summer', 'snow_dry_summer_warm_summer', 'snow_dry_summer_hot_summer', 'snow_dry_summer_cold_summer', 'mild_temperate_dry_winter_cool_summer']. The values stored in these columns represent corresponding proportions of climate profiles within the grid area. |
| `Mean Elevation` | The average elevation of the grid area. |

#### `images/img_relief`
A folder including Earth relief images for each 1degree * 1degree grid region across the globe (with a total of 360*180=64800 grids). Incorporation of these materials supplement spatio-temporal data analysis and spatial intelligence research.

| File | Description |
|---|---|
| `relief_xxN/S_xxE/W.png` | Geo-image containing observed topography and terrain inferred through height gravity. All files in the folder are named in the format relief_yyN/S_zzE/W.png. This indicates that the Earth relief image is located with the rectangular upper-right corner at the [yy, zz] latitude and longitude coordinates. |
