# ILI Time Series Forecasting

## Task Description

You are solving a machine learning task of time series forecasting using the ILI (Influenza-Like Illness) dataset.

The dataset presented here comprises real-world time series data tracking influenza-like illness statistics. We have split the dataset into train, validation, and test parts.

## Data Description

- **Input**: A sequence of past observations (INPUT_SEQ_LEN=36, INPUT_DIM=7)
- **Output**: Predict the next future sequence (PRED_SEQ_LEN=24, PRED_DIM=7)
- **Evaluation Metrics**: Mean Squared Error (MSE) and Mean Absolute Error (MAE)

The dataset contains 7 features from the CDC's influenza surveillance system:
1. % WEIGHTED ILI
2. % UNWEIGHTED ILI
3. AGE 0-4
4. AGE 5-24
5. ILITOTAL
6. NUM. OF PROVIDERS
7. OT (Other)




## Submission Format

The submission should be a CSV file with the following format:
- Column `id`: Integer index for each test sample (0 to N_test-1)
- Columns `pred_0` to `pred_167`: Flattened predictions (24 timesteps × 7 features = 168 values per sample)

Example CSV structure:
```
id,pred_0,pred_1,pred_2,...,pred_166,pred_167
0,0.5,0.3,0.7,...,0.2,0.4
1,0.6,0.4,0.8,...,0.3,0.5
...
```


## Evaluation

Your predictions will be evaluated using two metrics:
1. **MSE (Mean Squared Error)**: Lower is better
2. **MAE (Mean Absolute Error)**: Lower is better

The primary ranking metric is MSE.

## Goal

Train a time series forecasting model to accurately predict future ILI statistics based on historical observations.

## Notes

- This is a multivariate time series forecasting problem
- Each input sequence covers 36 weeks of data
- You need to predict the next 24 weeks
- All 7 features need to be predicted simultaneously
- The data has been preprocessed and standardized

