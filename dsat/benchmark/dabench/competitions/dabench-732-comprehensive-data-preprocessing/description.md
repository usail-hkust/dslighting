# DABench Task 732 - Perform comprehensive data preprocessing for the dataset by handling missing values in the life expectancy column. Choose an appropriate strategy and implement it using Python code.

## Task Description

Perform comprehensive data preprocessing for the dataset by handling missing values in the life expectancy column. Choose an appropriate strategy and implement it using Python code.

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `gapminder_cleaned.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Assume there are missing values in the life expectancy column.
Impute missing values with the mean life expectancy of the same country.
If there are countries with all life expectancy values missing, replace missing values with the mean life expectancy of the entire dataset.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@number_of_missing_values_in_lifeexp_after[n_after]

where "n_after" is an integer representing the number of missing values in the life expectancy column after the imputation process.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
