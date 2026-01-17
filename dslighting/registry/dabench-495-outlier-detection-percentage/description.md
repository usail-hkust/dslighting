# DABench Task 495 - Perform outlier detection on the percentage of graduates in the field of Architecture over the years using the Z-score method with a threshold of 3. Identify all years with outliers, then calculate the mean and standard deviation for the years without these outliers.

## Task Description

Perform outlier detection on the percentage of graduates in the field of Architecture over the years using the Z-score method with a threshold of 3. Identify all years with outliers, then calculate the mean and standard deviation for the years without these outliers.

## Concepts

Outlier Detection, Summary Statistics

## Data Description

Dataset file: `percent-bachelors-degrees-women-usa.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Z-score method with a threshold of 3 for outlier detection.
Include all years in the dataset for the calculation.
After identifying the outliers, remove them and then calculate the mean percentage and the standard deviation of the remaining data. Round to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@std_without_outliers[std_value] @mean_without_outliers[mean_value]

"mean_value" and "std_value" are floating point numbers rounded to two decimals representing the mean and standard deviation after removing outliers.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
