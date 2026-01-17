# DABench Task 492 - Which field has the highest percentage of graduates in the year 2010?

## Task Description

Which field has the highest percentage of graduates in the year 2010?

## Concepts

Summary Statistics

## Data Description

Dataset file: `percent-bachelors-degrees-women-usa.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Compare the last available data points (year 2010) for all fields within the dataset. If fields share the maximum percentage value, return all those fields separated by commas.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@fields[field_names]

"field_names" is string(s) separated by commas, mentioning field(s) with the highest percentage of graduates in the year 2010.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
