# DABench Task 508 - 3. Is there a correlation between the number of reviews a hotel has received and its bubble score? If yes, what is the correlation coefficient?

## Task Description

3. Is there a correlation between the number of reviews a hotel has received and its bubble score? If yes, what is the correlation coefficient?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `hotel_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient between review count and bubble score. Consider the correlation to be significant if its absolute value is greater than 0.5. Round your result to three decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_coefficient[r_value]

"r_value" is a number between -1 and 1, rounded to three decimal places, representing the correlation between the review count and the bubble score.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
