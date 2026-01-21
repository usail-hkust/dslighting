# DABench Task 140 - Question 3: Is there a correlation between the number of votes received by the Democratic and Republican parties? If so, is it a linear or nonlinear relationship?

## Task Description

Question 3: Is there a correlation between the number of votes received by the Democratic and Republican parties? If so, is it a linear or nonlinear relationship?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `election2016.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Calculate the Pearson correlation coefficient (r) between 'votes_dem' and 'votes_gop'.
Report if the correlation is significant using a two-tailed test with a significance level (alpha) of 0.05.
If p-value is less than 0.05 and absolute r >= 0.5, define it as a significant linear relationship.
If p-value is less than 0.05 and absolute r < 0.5, define it as a significant nonlinear relationship.
If p-value >= 0.05, define it as no significant relationship.}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `140`
- `answer`: two key-value pairs separated by a space: `@correlation_coefficient[<r_value>] @relationship_type[<relationship_type>]`

`<r_value>` is between -1 and 1 (three decimals); `<relationship_type>` is `linear`, `nonlinear`, or `none`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
