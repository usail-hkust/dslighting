# DABench Task 665 - Perform data preprocessing by filling the missing values with the mean values of their respective columns. After that, create a new column called 'Price Category' that categorizes the 'Close' prices into 'High', 'Medium', and 'Low'. 'High' is represented by 'Close' prices that are greater than or equal to the 75th percentile of the 'Close' column data; 'Medium' is represented by 'Close' prices that are between the 25th to 75th percentile; 'Low' is represented by 'Close' prices that are less than or equal to the 25th percentile. Calculate the count and proportion of each category in the dataset.

## Task Description

Perform data preprocessing by filling the missing values with the mean values of their respective columns. After that, create a new column called 'Price Category' that categorizes the 'Close' prices into 'High', 'Medium', and 'Low'. 'High' is represented by 'Close' prices that are greater than or equal to the 75th percentile of the 'Close' column data; 'Medium' is represented by 'Close' prices that are between the 25th to 75th percentile; 'Low' is represented by 'Close' prices that are less than or equal to the 25th percentile. Calculate the count and proportion of each category in the dataset.

## Concepts

Comprehensive Data Preprocessing, Feature Engineering, Summary Statistics

## Data Description

Dataset file: `YAHOO-BTC_USD_D.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Constraints:
1. Fill missing values using the mean of their respective columns.
2. Define the three categories (High, Medium, Low) based on the percentiles as specified.
3. Calculate the count and proportion of each category up to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@high_count[high_count] @high_proportion[high_proportion] @medium_count[medium_count] @medium_proportion[medium_proportion] @low_count[low_count] @low_proportion[low_proportion]

"high_count", "medium_count", and "low_count" are positive integers. "high_proportion", "medium_proportion", and "low_proportion" are numbers between 0 and 1, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
