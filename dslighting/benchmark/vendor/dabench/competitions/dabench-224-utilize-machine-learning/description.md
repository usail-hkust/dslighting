# DABench Task 224 - Utilize machine learning techniques to classify the sites into two categories based on their positive_diffsel values, with values less than or equal to the mean defined as 'low' selection, and the rest as 'high'. Split the dataset into training and testing sets with an 80:20 ratio using a specified random state of 42. Train a logistic regression model on the training set, and evaluate its performance on the testing set using accuracy as a metric.

## Task Description

Utilize machine learning techniques to classify the sites into two categories based on their positive_diffsel values, with values less than or equal to the mean defined as 'low' selection, and the rest as 'high'. Split the dataset into training and testing sets with an 80:20 ratio using a specified random state of 42. Train a logistic regression model on the training set, and evaluate its performance on the testing set using accuracy as a metric.

## Concepts

Machine Learning, Distribution Analysis

## Data Description

Dataset file: `ferret-Pitt-2-preinf-lib2-100_sitediffsel.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use scikit-learn's Logistic Regression for your classifier model, 'liblinear' solver for the Logistic Regression, and a random state of 42 when splitting the data and building the model. All numeric values should be rounded to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `224`
- `answer`: `@accuracy_score[<float between 0 and 1>]` rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
