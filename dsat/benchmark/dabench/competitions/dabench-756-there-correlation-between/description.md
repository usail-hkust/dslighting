# DABench Task 756 - 2. Is there a correlation between the maximum temperature (TMAX_F) and the observation values (obs_value)? If yes, what is the correlation coefficient?

## Task Description

2. Is there a correlation between the maximum temperature (TMAX_F) and the observation values (obs_value)? If yes, what is the correlation coefficient?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `weather_data_1864.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient(r) to assess the strength and direction of the linear relationship between TMAX_F and obs_value. Conduct the test at a significance level (alpha) of 0.05. If the p-value is less than 0.05, report the p-value and r-value. If the p-value is greater than or equal to 0.05, report that there is no significant correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@correlation_coefficient[r_value] @p_value[p_value]

"r_value" is between -1 and 1, rounded to two decimal places; "p_value" is between 0 and 1, rounded to four decimal places. If there is no significant correlation, output @correlation_status["No significant correlation"] instead.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
