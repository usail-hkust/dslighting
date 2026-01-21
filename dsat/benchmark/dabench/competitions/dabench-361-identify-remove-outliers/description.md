# DABench Task 361 - Identify and remove outliers in the wind speed column of the weather dataset. Use the Z-score method to detect outliers with a threshold of 3 and create a new dataframe without the outlier values.

## Task Description

Identify and remove outliers in the wind speed column of the weather dataset. Use the Z-score method to detect outliers with a threshold of 3 and create a new dataframe without the outlier values.

## Concepts

Outlier Detection, Comprehensive Data Preprocessing

## Data Description

Dataset file: `weather_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Use a Z-score threshold of 3 for outlier identification.
If the Z-score of a value is higher than 3 or lower than -3, consider it as an outlier.
After outlier detection, drop these rows and create a new dataframe.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `361`
- `answer`: `@outlier_count[<integer>]` where `<integer>` is the total outlier count.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
