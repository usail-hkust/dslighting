# DABench Task 656 - 3. Perform an outlier analysis on the X-coordinate column using the Z-score method. Identify any outliers based on a threshold of 3 standard deviations from the mean. Then, remove the outliers from the dataset and calculate the new mean and standard deviation of the X-coordinate column.

## Task Description

3. Perform an outlier analysis on the X-coordinate column using the Z-score method. Identify any outliers based on a threshold of 3 standard deviations from the mean. Then, remove the outliers from the dataset and calculate the new mean and standard deviation of the X-coordinate column.

## Concepts

Outlier Detection, Summary Statistics

## Data Description

Dataset file: `DES=+2006261.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate Z-scores for each value in the X-coordinate column.
Identify outliers based on a threshold of Z-score greater than 3 or less than -3.
Remove the identified outliers from the dataset.
Calculate the new mean and standard deviation for the updated X-coordinate column.
Report the number of identified outliers, the new mean and the new standard deviation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@number_of_outliers[number_of_outliers] @new_mean[new_mean_value] @new_standard_deviation[new_sd_value]

"number_of_outliers" is an integer. "new_mean_value" and "new_sd_value" are numbers rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
