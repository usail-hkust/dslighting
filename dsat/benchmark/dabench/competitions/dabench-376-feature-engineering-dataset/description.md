# DABench Task 376 - 3. Perform feature engineering on the dataset by creating a new column called "Trips per Membership". Calculate the number of trips per membership for each date and store the result in the new column. Determine the mean and median of the "Trips per Membership" column. Compare the values with the mean and median of the "Trips over the past 24-hours (midnight to 11:59pm)" column to analyze the impact of membership on trip frequency.

## Task Description

3. Perform feature engineering on the dataset by creating a new column called "Trips per Membership". Calculate the number of trips per membership for each date and store the result in the new column. Determine the mean and median of the "Trips per Membership" column. Compare the values with the mean and median of the "Trips over the past 24-hours (midnight to 11:59pm)" column to analyze the impact of membership on trip frequency.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `2014_q4.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

The "Trips per Membership" is calculated as the ratio of "Trips over the past 24-hours (midnight to 11:59pm)" to "Total Annual Memberships Sold". Be sure to handle divisions by zero appropriately by replacing the infinity values with zero. Calculate the mean and median using Python's pandas library functions with all final results must be rounded off to 2 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `376`
- `answer`: three key-value pairs separated by spaces: `@trips_per_membership_median[<median>] @trips_per_day_mean[<mean>] @trips_per_membership_mean[<mean>]`

Each value is a float rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
