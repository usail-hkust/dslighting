# DABench Task 734 - Is there a correlation between life expectancy and GDP per capita for each continent? Perform correlation analysis for each continent separately and provide the correlation coefficients.

## Task Description

Is there a correlation between life expectancy and GDP per capita for each continent? Perform correlation analysis for each continent separately and provide the correlation coefficients.

## Concepts

Correlation Analysis, Comprehensive Data Preprocessing

## Data Description

Dataset file: `gapminder_cleaned.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between life expectancy and GDP per capita for each continent. Assess the correlation significance using a two-tailed test with a significance level (alpha) of 0.05. Report the p-values associated with the correlation test. Consider the correlation significant if the p-value is less than 0.05 and the absolute value of r is greater than or equal to 0.5. Consider the correlation non-significant if the p-value is greater than or equal to 0.05.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@correlation_coefficient[r_value] @correlation_significance[significance]

"r_value" is a number between -1 and 1, rounded appropriately. "significance" is either "significant" or "non-significant".

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
