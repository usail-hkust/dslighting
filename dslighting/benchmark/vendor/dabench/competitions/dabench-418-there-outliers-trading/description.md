# DABench Task 418 - 3. Are there any outliers in the trading volume of the asset or commodity? If yes, how can they be detected?

## Task Description

3. Are there any outliers in the trading volume of the asset or commodity? If yes, how can they be detected?

## Concepts

Outlier Detection

## Data Description

Dataset file: `bitconnect_price.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Convert 'Volume' column to numerical values. Calculate the Z-scores for the 'Volume' column. Assume values with Z-scores greater than 3 or less than -3 as outliers. Calculate the absolute number of outliers.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@outliers_count[value]

'value' is an integer.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
