# DABench Task 249 - Is there a significant correlation between the number of doubles hit by a player and their salary? If so, what is the correlation coefficient and p-value?

## Task Description

Is there a significant correlation between the number of doubles hit by a player and their salary? If so, what is the correlation coefficient and p-value?

## Concepts

Correlation Analysis, Summary Statistics

## Data Description

Dataset file: `baseball_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between the number of doubles hit and player's salary. Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05. Report the p-value associated with the correlation test. Consider the relationship to be significant if the p-value is less than 0.05. If the p-value is greater than or equal to 0.05, report that there is no significant correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `249`
- `answer`: `@correlation_coefficient[<r_value>]` where `<r_value>` is between -1 and 1 (two decimals).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
