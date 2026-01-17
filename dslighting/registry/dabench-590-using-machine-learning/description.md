# DABench Task 590 - Using machine learning techniques, can we predict the number of agents needed to handle incoming calls based on the timestamp and other available information? If so, predict the number for the timestamp "20170413_120000".

## Task Description

Using machine learning techniques, can we predict the number of agents needed to handle incoming calls based on the timestamp and other available information? If so, predict the number for the timestamp "20170413_120000".

## Concepts

Machine Learning

## Data Description

Dataset file: `20170413_000000_group_statistics.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use a simple linear regression model for prediction. The model should be trained with features such as the timestamp, number of calls answered, number of call abandoned, etc., and the target variable should be the average number of agents staffed. Perform prediction for the given timestamp after training the model.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `590`
- `answer`: `@predicted_agents[<predicted_num_agents>]` where `<predicted_num_agents>` is a non-negative integer predicted for the specified timestamp.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
