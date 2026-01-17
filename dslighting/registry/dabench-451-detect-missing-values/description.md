# DABench Task 451 - 3. Can you detect any missing values in the dataset? If yes, how many missing values are there for each column?

## Task Description

3. Can you detect any missing values in the dataset? If yes, how many missing values are there for each column?

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `baro_2015.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

The columns are ["DATE TIME", "WINDSPEED", "DIR", "GUSTS", "AT", "BARO", "RELHUM", "VIS"].

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@missing_values_per_column[{'DATE TIME':val_1, 'WINDSPEED':val_2, 'DIR':val_3, 'GUSTS':val_4, 'AT':val_5, 'BARO':val_6, 'RELHUM':val_7, 'VIS':val_8}]

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
