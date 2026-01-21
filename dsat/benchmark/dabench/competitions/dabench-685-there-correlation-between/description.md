# DABench Task 685 - 3. Is there a correlation between the atmospheric pressure and wind speed in the dataset?

## Task Description

3. Is there a correlation between the atmospheric pressure and wind speed in the dataset?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `ravenna_250715.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between atmospheric pressure and wind speed. Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05. Report the p-value associated with the correlation test. Consider the relationship to be significant if the p-value is less than 0.05.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@correlation_coefficient[r_value] @relationship_significance[significance] @p_value[value]

"r_value" is a number between -1 and 1, rounded to two decimal places. "value" is the p-value rounded to four decimals. "significance" is "significant" or "not significant" based on the p-value.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
