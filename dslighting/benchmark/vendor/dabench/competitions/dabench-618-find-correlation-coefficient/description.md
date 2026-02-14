# DABench Task 618 - 3. Find the correlation coefficient between the number of photos taken during the trajectories and the total duration spent at each point of interest. Use the Python Pandas library's corr() function for the calculation.

## Task Description

3. Find the correlation coefficient between the number of photos taken during the trajectories and the total duration spent at each point of interest. Use the Python Pandas library's corr() function for the calculation.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `traj-Osak.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient between the number of photos and the total duration spent at each point of interest using pandas' corr() function.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation[corr]

where "corr" is a number between -1 and 1 rounded to three decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
