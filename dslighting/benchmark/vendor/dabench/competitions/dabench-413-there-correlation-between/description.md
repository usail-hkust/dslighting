# DABench Task 413 - Is there a correlation between the ticket class (Pclass) and the fare paid by the passengers that embarked from Cherbourg (Embarked = 'C')?

## Task Description

Is there a correlation between the ticket class (Pclass) and the fare paid by the passengers that embarked from Cherbourg (Embarked = 'C')?

## Concepts

Correlation Analysis, Comprehensive Data Preprocessing

## Data Description

Dataset file: `titanic_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between Pclass and Fare for passengers who embarked from Cherbourg.
Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.01.
Report the p-value associated with the correlation test.
Consider the relationship to be significant if the p-value is less than 0.01.
If the p-value is greater than or equal to 0.01, report that there is no significant correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@correlation_coefficient[r_value] @relationship_significance[significance] @p_value[p_value]

"r_value" is between -1 and 1, rounded to two decimal places. "p_value" is between 0 and 1, rounded to four decimal places. "significance" is "significant" or "not significant" based on the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
