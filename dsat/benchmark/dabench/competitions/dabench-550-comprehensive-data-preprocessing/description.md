# DABench Task 550 - Perform comprehensive data preprocessing on the abalone dataset. Handle any missing values and scale the variables (length, diameter, height, whole weight, shucked weight, viscera weight, shell weight) using min-max normalization. Then, perform a distribution analysis to determine if the scaled variables adhere to a normal distribution.

## Task Description

Perform comprehensive data preprocessing on the abalone dataset. Handle any missing values and scale the variables (length, diameter, height, whole weight, shucked weight, viscera weight, shell weight) using min-max normalization. Then, perform a distribution analysis to determine if the scaled variables adhere to a normal distribution.

## Concepts

Comprehensive Data Preprocessing, Distribution Analysis

## Data Description

Dataset file: `abalone.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Any missing values should be filled using the median of the respective column. Use sklearn's MinMaxScaler for normalization, scale the variables to a range between 0 and 1. For distribution analysis, use skewness and kurtosis to determine the distribution type. If skewness is between -0.5 and 0.5 and kurtosis is between -2 and 2, we consider it as normal.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `550`
- `answer`: three key-value pairs separated by spaces: `@distribution_type[<distribution type>] @min_max_scaler_scale[<range>] @missing_values_handled[<Yes/No>]`

`<distribution type>` is `Normal` or `Non-Normal`; `<range>` describes the scaler range (e.g., `0-1`); `<Yes/No>` indicates whether missing values were handled.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
