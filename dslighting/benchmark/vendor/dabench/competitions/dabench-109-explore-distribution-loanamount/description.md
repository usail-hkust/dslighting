# DABench Task 109 - Explore the distribution of the LoanAmount column based on different values of the Education column. Determine if there is a significant difference in the loan amount between individuals with different educational backgrounds.

## Task Description

Explore the distribution of the LoanAmount column based on different values of the Education column. Determine if there is a significant difference in the loan amount between individuals with different educational backgrounds.

## Concepts

Distribution Analysis, Feature Engineering

## Data Description

Dataset file: `test_Y3wMUE5_7gLdaTN.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean of LoanAmount for individuals with a 'Graduate' educational background and individuals with a 'Not Graduate' educational background separately. Test if there is a significant difference between these two groups using a t-test with a significance level (alpha) of 0.05. If the p-value is less than 0.05, report there is a significant difference, else report there is no significant difference.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `109`
- `answer`: three key-value pairs separated by spaces: `@graduate_mean_loan[<mean>] @not_graduate_mean_loan[<mean>] @significance[<significant/no significant>]`

Means are floats rounded to two decimals; significance indicates if the difference is significant at 0.05.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
