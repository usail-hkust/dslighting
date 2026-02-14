# DABench Task 419 - 1. Is there a significant difference in the mean opening prices between weekdays and weekends? Provide statistical evidence to support your answer.

## Task Description

1. Is there a significant difference in the mean opening prices between weekdays and weekends? Provide statistical evidence to support your answer.

## Concepts

Summary Statistics, Distribution Analysis

## Data Description

Dataset file: `bitconnect_price.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean opening prices separately for weekdays (Monday to Friday) and weekends (Saturday and Sunday). Conduct a two-sample t-test to check if there is a statistically significant difference between these two means. Use a significance level (alpha) of 0.05. If the p-value is less than 0.05, conclude that there is a significant difference. If the p-value is greater than or equal to 0.05, conclude that there is no significant difference.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@weekday_mean_price[weekday_mean_open_price] @weekend_mean_price[weekend_mean_open_price] @p_value[p_value] @significance[significant_or_not]

"weekday_mean_open_price" and "weekend_mean_open_price" are numbers rounded to two decimal places. "p_value" is between 0 and 1, rounded to four decimals. "significant_or_not" is 'Yes' or 'No' depending on whether the p-value is less than 0.05.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
