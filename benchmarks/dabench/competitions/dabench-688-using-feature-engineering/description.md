# DABench Task 688 - 3. Using feature engineering, create a new feature called "time_of_day" based on the "dt" column. The "time_of_day" feature should categorize the timestamp into morning (6:00 to 11:59), afternoon (12:00 to 17:59), evening (18:00 to 23:59), and night (0:00 to 5:59) (included). Provide the count of each category in the "time_of_day" column.

## Task Description

3. Using feature engineering, create a new feature called "time_of_day" based on the "dt" column. The "time_of_day" feature should categorize the timestamp into morning (6:00 to 11:59), afternoon (12:00 to 17:59), evening (18:00 to 23:59), and night (0:00 to 5:59) (included). Provide the count of each category in the "time_of_day" column.

## Concepts

Feature Engineering

## Data Description

Dataset file: `ravenna_250715.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

For each time of the day, include the first minute of each category and exclude the first minute of the next category. If there's multiple entry which belongs to the same minute, account them all into the corresponding category.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@morning[morning_count] @afternoon[afternoon_count]

Counts are integers for the morning and afternoon categories.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
