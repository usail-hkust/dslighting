# Ethanol Concentration Time Series Classification

## Task Description

You are solving a machine learning task of time series classification using the Ethanol Concentration dataset.

The dataset presented here comprises real-world time series data. We have split the dataset into train and test parts.

## Data Description

- **Input**: A sequence of observed features (SEQUENCE_LENGTH=1751, FEATURE_DIM=3)
- **Output**: Predict the labels for the given sequence, where the label is in range of {0, 1, 2, 3} (4 classes total)
- **Evaluation Metric**: Accuracy

## Files

- `train_data.npy` - Training features in numpy format (shape: [N_train, 1751, 3])
- `train_labels.npy` - Training labels in numpy format (shape: [N_train,])
- `test_data.npy` - Test features in numpy format (shape: [N_test, 1751, 3])
- `sample_submission.csv` - Sample submission file showing the required format

## Data Loading

You can load the data using numpy:

```python
import numpy as np

# Load training data
X_train = np.load('train_data.npy')
y_train = np.load('train_labels.npy')

# Load test data
X_test = np.load('test_data.npy')

print(f"X_train shape: {X_train.shape}")  # (N_train, 1751, 3)
print(f"y_train shape: {y_train.shape}")  # (N_train,)
print(f"X_test shape: {X_test.shape}")    # (N_test, 1751, 3)
```

## Submission Format

The submission file should contain predictions for each test sample:
- Column `id`: Integer index for each test sample
- Column `label`: Predicted class label (integer in range [0, 3])

Example:
```
id,label
0,2
1,0
2,3
...
```

## Goal

Train a time series classification model to achieve good performance on the test set as measured by accuracy.

## Notes

- The dataset contains real-world time series data for ethanol concentration classification
- Each sample is a multivariate time series with 3 features observed over 1751 time steps
- There are 4 distinct classes to predict
