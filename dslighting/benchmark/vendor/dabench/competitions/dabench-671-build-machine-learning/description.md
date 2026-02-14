# DABench Task 671 - Build a machine learning model to predict the MedianHouseValue based on the following features:
1. MedInc
2. AveRooms
3. Population
4. Latitude
5. Longitude
Split the dataset into training and testing sets, train the model using linear regression, and evaluate its performance using mean squared error (MSE).

## Task Description

Build a machine learning model to predict the MedianHouseValue based on the following features:
1. MedInc
2. AveRooms
3. Population
4. Latitude
5. Longitude
Split the dataset into training and testing sets, train the model using linear regression, and evaluate its performance using mean squared error (MSE).

## Concepts

Machine Learning

## Data Description

Dataset file: `my_test_01.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Split the dataset into 70% for training and 30% for testing. Use linear regression for the machine learning model. Calculate the MSE to three decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@mse[mse_value]

"mse_value" is a float rounded to three decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
