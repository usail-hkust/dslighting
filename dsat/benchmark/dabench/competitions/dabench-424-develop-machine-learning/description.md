# DABench Task 424 - 3. Develop a machine learning model to classify the asset or commodity into different price categories (low, medium, high) based on the opening, high, and low prices. The boundaries for the categories are: Low(< 500), Medium(500 - 1000), High(> 1000). What are the accuracy of the model and the top three contributing features to the classification?

## Task Description

3. Develop a machine learning model to classify the asset or commodity into different price categories (low, medium, high) based on the opening, high, and low prices. The boundaries for the categories are: Low(< 500), Medium(500 - 1000), High(> 1000). What are the accuracy of the model and the top three contributing features to the classification?

## Concepts

Machine Learning, Feature Engineering

## Data Description

Dataset file: `bitconnect_price.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use a Random Forest Classifier for the model and split the data into a 75% training set and 25% test set. Use out-of-the-box settings for the model. The accuracy should be calculated on the test set. Measures of feature importance should be based on the Gini importance or mean decrease impurity.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@feature2[feature_name]

The grader only checks this marker. "feature_name" is the name of the most important feature.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
