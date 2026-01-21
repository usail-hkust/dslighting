# Handwriting Time Series Classification

## Task Description

You are solving a machine learning task of time series classification using the Handwriting dataset.

The dataset presented here comprises real-world time series data. We have split the dataset into train and test parts.

## Data Description

- **Input**: A sequence of observed features (SEQUENCE_LENGTH=152, FEATURE_DIM=3)
- **Output**: Predict the labels for the given sequence, where the label is in range of {0, 1, ..., 25} (26 classes total)
- **Evaluation Metric**: Accuracy

## Files

- `train_data.npy` - Training features as a dense NumPy array of shape `(150, 152, 3)`
- `train_labels.npy` - Training labels as integers in `[0, 25]` with shape `(150,)`
- `test_data.npy` - Test features as a dense NumPy array of shape `(850, 152, 3)`
- `sample_submission.csv` - Sample submission file showing the required format

## Submission Format

The submission file should contain predictions for each test sample:
- Column `id`: Integer index for each test sample
- Column `label`: Predicted class label (integer in range [0, 25])

Example:
```
id,label
0,5
1,12
2,3
...
```

## Goal

Train a time series classification model to achieve good performance on the test set as measured by accuracy.
