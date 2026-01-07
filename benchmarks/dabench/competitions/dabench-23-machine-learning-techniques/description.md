# DABench Task 23 - Apply machine learning techniques to predict the employment level in March 2020 based on the data from March 2019. Split the dataset into a 70-30 split for training and testing sets, train a simple linear regression model on the training set, and evaluate its performance on the testing set using Mean Squared Error as the evaluation metric.

## Task Description

Apply machine learning techniques to predict the employment level in March 2020 based on the data from March 2019. Split the dataset into a 70-30 split for training and testing sets, train a simple linear regression model on the training set, and evaluate its performance on the testing set using Mean Squared Error as the evaluation metric.

## Concepts

Machine Learning, Summary Statistics

## Data Description

Dataset file: `unemployement_industry.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Split the dataset with a 70-30 split for training and testing sets with a random seed of 42. Use a simple linear regression model for training and evaluate the model's performance by calculating the Mean Squared Error.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `23`
- `answer`: `@Mean_Squared_Error[<MSE>]` where `<MSE>` is rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
