# DABench Task 575 - Using feature engineering techniques, create a new feature that represents the average stock price of Apple Inc. (AAPL), Microsoft Corporation (MSFT), and Amazon.com, Inc. (AMZN) on the given dates. Calculate the correlation between this new feature and the closing value of the S&P 500 Index (.SPX).

## Task Description

Using feature engineering techniques, create a new feature that represents the average stock price of Apple Inc. (AAPL), Microsoft Corporation (MSFT), and Amazon.com, Inc. (AMZN) on the given dates. Calculate the correlation between this new feature and the closing value of the S&P 500 Index (.SPX).

## Concepts

Feature Engineering, Correlation Analysis

## Data Description

Dataset file: `tr_eikon_eod_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between the newly created average stock price feature and the closing value of the S&P 500 Index (.SPX).
Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05.
Report the p-value associated with the correlation test.
Consider the relationship to be linear if the p-value is less than 0.05 and the absolute value of r is greater than or equal to 0.5.
Consider the relationship to be nonlinear if the p-value is less than 0.05 and the absolute value of r is less than 0.5.
If the p-value is greater than or equal to 0.05, report that there is no significant correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `575`
- `answer`: three key-value pairs separated by spaces: `@relationship_type_relation[<relationship_type>] @p_value_pval[<p_value>] @correlation_coefficient_corr[<r_value>]`

`<r_value>` is between -1 and 1 (two decimals), `<p_value>` is between 0 and 1 (four decimals), and `<relationship_type>` is `linear`, `nonlinear`, or `none`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
