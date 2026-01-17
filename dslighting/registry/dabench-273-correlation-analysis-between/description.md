# DABench Task 273 - Perform a correlation analysis between the MEANGAM and MEANGBT columns. Additionally, for the correlated variables, identify any outliers in the MEANGAM column using the Z-score method and a threshold of 3 for the absolute Z-score.

## Task Description

Perform a correlation analysis between the MEANGAM and MEANGBT columns. Additionally, for the correlated variables, identify any outliers in the MEANGAM column using the Z-score method and a threshold of 3 for the absolute Z-score.

## Concepts

Correlation Analysis, Outlier Detection

## Data Description

Dataset file: `3901.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

1. Use the Pearson correlation coefficient to assess the correlation between MEANGAM and MEANGBT columns.
2. Define outliers as those data points in the MEANGAM column where the absolute Z-score exceeds 3.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `273`
- `answer`: three key-value pairs separated by spaces: `@correlation_coefficient[<correlation_value>] @outlier_count[<outlier_total>] @outlier_list[<outlier_values_list>]`

`<correlation_value>` is between -1 and 1 (three decimals); `<outlier_total>` is an integer; `<outlier_values_list>` is a comma-separated list of MEANGAM outlier values (two decimals).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
