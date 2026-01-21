# DABench Task 308 - Use feature engineering techniques to create a new variable "Title" by extracting the title from the Name column (e.g., "Mr.", "Mrs.", "Miss"). Only consider the following titles: 'Mr.', 'Mrs.', 'Miss.' and 'Master.' (titles followed by a dot). Then, calculate the average fare for each unique title to two decimal places.

## Task Description

Use feature engineering techniques to create a new variable "Title" by extracting the title from the Name column (e.g., "Mr.", "Mrs.", "Miss"). Only consider the following titles: 'Mr.', 'Mrs.', 'Miss.' and 'Master.' (titles followed by a dot). Then, calculate the average fare for each unique title to two decimal places.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Only the titles 'Mr.', 'Mrs.', 'Miss.' and 'Master.' should be considered. Titles that do not fall within these four categories should be eliminated.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `308`
- `answer`: two key-value pairs separated by a space: `@average_fare_Mrs[<fare>] @average_fare_Mr[<fare>]`

Each `<fare>` is the average fare for that title, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
