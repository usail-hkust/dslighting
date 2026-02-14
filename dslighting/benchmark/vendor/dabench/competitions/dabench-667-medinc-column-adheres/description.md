# DABench Task 667 - Check if the MedInc column adheres to a normal distribution in the provided dataset.

## Task Description

Check if the MedInc column adheres to a normal distribution in the provided dataset.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `my_test_01.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Perform a Shapiro-Wilk test at a significance level (alpha) of 0.05 to assess normality of the MedInc column. Report the p-value associated with the normality test. If the p-value is greater than 0.05, state that the data is normally distributed. If the p-value is less than or equal to 0.05, state that the data is not normally distributed.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@distribution_type[distribution_type]

"distribution_type" is either "normal" or "not normal" based on the conditions specified in the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
