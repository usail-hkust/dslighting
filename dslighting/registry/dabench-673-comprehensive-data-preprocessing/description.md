# DABench Task 673 - Apply comprehensive data preprocessing on the dataset by following these steps:
1. Replace any missing values in the MedInc column with the mean value.
2. Standardize the values in the AveOccup column using z-scores.
3. Create a new feature called "RoomsPerPerson" by dividing the AveRooms column by the Population column.
4. Calculate the Pearson correlation coefficient between the MedianHouseValue and RoomsPerPerson columns.
5. Finally, calculate the mean and standard deviation of the MedianHouseValue column.

## Task Description

Apply comprehensive data preprocessing on the dataset by following these steps:
1. Replace any missing values in the MedInc column with the mean value.
2. Standardize the values in the AveOccup column using z-scores.
3. Create a new feature called "RoomsPerPerson" by dividing the AveRooms column by the Population column.
4. Calculate the Pearson correlation coefficient between the MedianHouseValue and RoomsPerPerson columns.
5. Finally, calculate the mean and standard deviation of the MedianHouseValue column.

## Concepts

Comprehensive Data Preprocessing, Feature Engineering, Correlation Analysis, Summary Statistics

## Data Description

Dataset file: `my_test_01.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use sklearn's StandardScaler for standardization. Use numpy to calculate the mean and standard deviation. Round all output to four decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@pearson_coefficient[correlation_coefficient] @mean_value[mean_MedianHouseValue]

"mean_MedianHouseValue" is the mean of the MedianHouseValue column rounded to four decimal places. "correlation_coefficient" is a float rounded to four decimal places representing the correlation between MedianHouseValue and RoomsPerPerson.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
