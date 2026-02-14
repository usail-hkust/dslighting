# DABench Task 760 - 6. For each station, are there any missing values in the observation values (obs_value)? If yes, which station has the most missing values and how many missing values does it have?

## Task Description

6. For each station, are there any missing values in the observation values (obs_value)? If yes, which station has the most missing values and how many missing values does it have?

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `weather_data_1864.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

In your analysis:
- Assume that missing values are represented as "NaN".
- Calculate the number of missing values for each station.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@most_missing_station_name["station_name"] @most_missing_station_count[num_missing_obs]

"station_name" is the station with the most missing observation values. "num_missing_obs" is the count of missing observation values (>= 0) for that station.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
