# DABench Task 684 - 2. Does the humidity level in the dataset adhere to a normal distribution?

## Task Description

2. Does the humidity level in the dataset adhere to a normal distribution?

## Concepts

Distribution Analysis

## Data Description

Dataset file: `ravenna_250715.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Shapiro-Wilk test with a significance level (alpha) of 0.05 to determine if the distribution of the humidity level adheres to a normal distribution. Report the p-value associated with the test. If the p-value is greater than 0.05, it can be considered as normally distributed; otherwise, it is not.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@distribution_type[type] @shapiro_p_value[value]

"value" is the p-value from the Shapiro-Wilk test, rounded to four decimal places. "type" is "normal" or "not normal" based on the p-value.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
