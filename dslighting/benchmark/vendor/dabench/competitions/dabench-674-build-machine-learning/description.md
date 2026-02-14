# DABench Task 674 - Build a machine learning model to predict the MedianHouseValue based on the following features:
1. MedInc
2. AveRooms
3. HouseAge
4. Latitude
5. Longitude
Perform the following steps:
1. Split the dataset into training and testing sets, where 70% of the dataset is used for training and 30% for testing. Set the random_state as 42 for reproducibility.
2. Preprocess the data by standardizing the numerical columns (MedInc, AveRooms, HouseAge, Latitude, Longitude).
3. Train a decision tree regression model on the training set, setting the max_depth to 5.
4. Evaluate the model's performance using mean absolute error (MAE) on the testing set.
5. Finally, calculate the Pearson correlation coefficient between the predicted and actual MedianHouseValue values on the testing set.

## Task Description

Build a machine learning model to predict the MedianHouseValue based on the following features:
1. MedInc
2. AveRooms
3. HouseAge
4. Latitude
5. Longitude
Perform the following steps:
1. Split the dataset into training and testing sets, where 70% of the dataset is used for training and 30% for testing. Set the random_state as 42 for reproducibility.
2. Preprocess the data by standardizing the numerical columns (MedInc, AveRooms, HouseAge, Latitude, Longitude).
3. Train a decision tree regression model on the training set, setting the max_depth to 5.
4. Evaluate the model's performance using mean absolute error (MAE) on the testing set.
5. Finally, calculate the Pearson correlation coefficient between the predicted and actual MedianHouseValue values on the testing set.

## Concepts

Machine Learning, Comprehensive Data Preprocessing, Correlation Analysis

## Data Description

Dataset file: `my_test_01.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the sklearn library for splitting the dataset, preprocessing, training the model, and calculation of MAE. Set the random_state to 42 when splitting the dataset. Use the Pearson method to compute the correlation coefficient. Round all output to four decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@pearson_coefficient[correlation_coefficient] @mean_absolute_error[mae_value]

"mae_value" is the MAE on the testing set rounded to four decimal places. "correlation_coefficient" is the correlation between predicted and actual MedianHouseValue values on the testing set, rounded to four decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
