# DABench Task 125 - Can we predict the number of people fully vaccinated per hundred people based on the total number of vaccinations administered and the number of people vaccinated per hundred people?

## Task Description

Can we predict the number of people fully vaccinated per hundred people based on the total number of vaccinations administered and the number of people vaccinated per hundred people?

## Concepts

Correlation Analysis, Machine Learning

## Data Description

Dataset file: `country_vaccinations.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Perform a multiple linear regression analysis using the total number of vaccinations administered and the number of people vaccinated per hundred people as predictors.
The dependent variable is the number of people fully vaccinated per hundred people.
Only consider data entries without null values in the three mentioned columns.
Use a significance level (alpha) of 0.05 for the predictors.
Consider the predictors to be significant if the p-value is less than 0.05.
Calculate the R-squared value of the model.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `125`
- `answer`: `@significant_predictor[<predictor_1,predictor_2>] @r_squared[<r_squared_value>]`

`predictor_1,predictor_2` can be `yes`/`no` combinations; `r_squared_value` is between 0 and 1, rounded to four decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
