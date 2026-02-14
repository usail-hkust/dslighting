# DABench Task 30 - Create a linear regression machine learning model using the Scikit-learn library to predict the medical charges based on the age and BMI of individuals. Evaluate the performance of the model using the Root Mean Square Error (RMSE) evaluation metric only.

## Task Description

Create a linear regression machine learning model using the Scikit-learn library to predict the medical charges based on the age and BMI of individuals. Evaluate the performance of the model using the Root Mean Square Error (RMSE) evaluation metric only.

## Concepts

Machine Learning, Feature Engineering

## Data Description

Dataset file: `insurance.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the linear regression model available in the Scikit-Learn library. Split the data into training and testing sets with 80% of the data used for training and 20% used for testing. Use a random state of 42 for the split. The predictor variables are 'age' and 'bmi', and the target variable is 'charges'. Implement RMSE for the model evaluation. Ignore any row with missing values present in these three columns for this analysis.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `30`
- `answer`: `@model_rmse[<RMSE_value>]`, a positive number rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
