# DABench Task 421 - 3. Perform comprehensive data preprocessing on the trading volume column. Handle any missing values and transform the data to a suitable format for further analysis.

## Task Description

3. Perform comprehensive data preprocessing on the trading volume column. Handle any missing values and transform the data to a suitable format for further analysis.

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `bitconnect_price.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Since it is explicitly stated that there are no missing values, this part can be skipped. For data transformation, convert the trading volume from a String to a numeric data type. After transformation, calculate the mean and median trading volumes.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@mean_volume[mean_volume]

"mean_volume" is the mean trading volume rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
