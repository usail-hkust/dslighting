# DABench Task 8 - Perform a distribution analysis on the 'Fare' column for each passenger class ('Pclass') separately. Calculate the mean, median, and standard deviation of the fare for each class. Interpret the results in terms of the different passenger classes.

## Task Description

Perform a distribution analysis on the 'Fare' column for each passenger class ('Pclass') separately. Calculate the mean, median, and standard deviation of the fare for each class. Interpret the results in terms of the different passenger classes.

## Concepts

Distribution Analysis, Summary Statistics

## Data Description

Dataset file: `test_ave.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Keep all numerical values rounded to 2 decimal points. The population standard deviation should be calculated.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `8`
- `answer`: eight key-value pairs separated by spaces: `@median_fare_class1[<val>] @median_fare_class2[<val>] @std_dev_fare_class1[<val>] @mean_fare_class3[<val>] @std_dev_fare_class2[<val>] @mean_fare_class2[<val>] @std_dev_fare_class3[<val>] @mean_fare_class1[<val>]`

Each value is a float rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
