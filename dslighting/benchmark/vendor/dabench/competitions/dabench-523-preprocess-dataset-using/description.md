# DABench Task 523 - Preprocess the dataset by using comprehensive data preprocessing techniques, including cleaning, transformation, and handling missing values. Remove duplicate rows, normalize the 'Fare' column by scaling between 0 and 1, impute missing values in the 'Age' column using k-Nearest Neighbors algorithm with k=3, and drop the 'Cabin' column due to high missing values. Finally, create a new feature called 'AgeGroup' by binning the passengers into different age groups: 'Child' (age<=12), 'Teenager' (12<age<=18), 'Adult' (18<age<=60) and 'Senior' (age>60). Report the number of passengers in each category.

## Task Description

Preprocess the dataset by using comprehensive data preprocessing techniques, including cleaning, transformation, and handling missing values. Remove duplicate rows, normalize the 'Fare' column by scaling between 0 and 1, impute missing values in the 'Age' column using k-Nearest Neighbors algorithm with k=3, and drop the 'Cabin' column due to high missing values. Finally, create a new feature called 'AgeGroup' by binning the passengers into different age groups: 'Child' (age<=12), 'Teenager' (12<age<=18), 'Adult' (18<age<=60) and 'Senior' (age>60). Report the number of passengers in each category.

## Concepts

Comprehensive Data Preprocessing, Feature Engineering

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use sklearn's MinMaxScaler to normalize the 'Fare' column. For the 'Age' column, use sklearn's KNeighborsClassifier to make imputations, and learn the nearest neighbors on the 'Fare' and 'Pclass' columns. The 'AgeGroup' category should be a string of 'Child', 'Teenager', 'Adult' or 'Senior' based on the age of the passenger.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `523`
- `answer`: string with two key-value pairs separated by a space: `@child_count[<child_count>] @senior_count[<senior_count>]`

Both values are non-negative integer counts.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
