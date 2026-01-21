# DABench Task 432 - 2. Can we predict the maximum sustained wind speed based on the recorded damage in USD and the minimum recorded pressure? What is the performance of the prediction model?

## Task Description

2. Can we predict the maximum sustained wind speed based on the recorded damage in USD and the minimum recorded pressure? What is the performance of the prediction model?

## Concepts

Machine Learning, Comprehensive Data Preprocessing

## Data Description

Dataset file: `cost_data_with_errors.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Use a linear regression model for prediction.
Use 80% of the dataset for training and the rest for testing.
Use Mean Squared Error (MSE) as the evaluation metric to assess the model's performance.
Handle missing values in the "max_sust_wind", "damage_USD", and "min_p" columns by imputing them with their respective column means.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@mean_squared_error[mse]

"mse" is the mean squared error of the model, rounded to four decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
