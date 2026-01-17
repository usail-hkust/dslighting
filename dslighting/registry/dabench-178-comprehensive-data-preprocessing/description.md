# DABench Task 178 - Perform comprehensive data preprocessing on the dataset. Handle missing values in the "Embarked" column by imputing them with the mode value. Normalize the "Fare" column using Min-Max scaling. Encode the categorical variable "Sex" using Label Encoding, where "male" is coded as 1 and "female" as 0. Calculate the number of each label after processing "Sex" and the minimum, maximum and mean of "Fare" after scaling.

## Task Description

Perform comprehensive data preprocessing on the dataset. Handle missing values in the "Embarked" column by imputing them with the mode value. Normalize the "Fare" column using Min-Max scaling. Encode the categorical variable "Sex" using Label Encoding, where "male" is coded as 1 and "female" as 0. Calculate the number of each label after processing "Sex" and the minimum, maximum and mean of "Fare" after scaling.

## Concepts

Comprehensive Data Preprocessing, Feature Engineering

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
"Embarked" missing values should be filled with the mode value.
"Fare" should be normalized using Min-Max scaling, where Min is the minimum value of "Fare" before scaling and Max is the maximum.
"Sex" should be encoded using Label Encoding, where "male" is 1 and "female" is 0.
Caculate the count of each label of "Sex" after encoding and the min, max and mean of "Fare" values after scaling.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `178`
- `answer`: two key-value pairs separated by a space: `@sex_encoded_count[<label_0_count, label_1_count>] @fare_after_scaling[<min_fare, max_fare, mean_fare>]`

`label_0_count` and `label_1_count` are counts; `min_fare` and `max_fare` rounded to two decimals; `mean_fare` rounded to four decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
