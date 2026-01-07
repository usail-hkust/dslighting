# DABench Task 522 - Perform feature engineering by creating a new feature called 'Title' from the 'Name' column, which represents the title (e.g., Mr., Mrs., Miss) of each passenger. Then, analyze the distribution of the 'Title' feature and check if it is correlated with the passenger class ('Pclass') using the chi-square test.

## Task Description

Perform feature engineering by creating a new feature called 'Title' from the 'Name' column, which represents the title (e.g., Mr., Mrs., Miss) of each passenger. Then, analyze the distribution of the 'Title' feature and check if it is correlated with the passenger class ('Pclass') using the chi-square test.

## Concepts

Feature Engineering, Distribution Analysis, Correlation Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Generate 'Title' by extracting the title before the period (.) in the 'Name' column, and the title is defined as a string that contains no spaces. For others which are not 'Mr.', 'Mrs.', 'Miss.', replace them with 'Other'. The degrees of freedom for the chi-square test are calculated as (r - 1) * (c - 1), where r equals the number of rows (categories in 'Title') and c equals the number of columns (categories in 'Pclass'). Use a significance level of 0.05.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@p_value[P-value]

"P-value" is between 0 and 1, rounded to four decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
