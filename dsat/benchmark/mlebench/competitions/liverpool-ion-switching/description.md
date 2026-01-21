# Liverpool Ion Switching

## Description

Ion channels are pore-forming proteins present in animals and plants that encode learning and memory, help fight infections, enable pain signals, and stimulate muscle contraction. When ion channels open, they pass electric currents. Scientists hope that machine learning can enable rapid automatic detection of ion channel current events in raw data.

In this competition, you'll use ion channel data to better model automatic identification methods. If successful, you'll be able to detect individual ion channel events in noisy raw signals.

## Evaluation

Submissions are evaluated using the **macro F1 score**.

F1 is calculated as follows:

$$F_1 = 2 \times \frac{\text{precision} \times \text{recall}}{\text{precision} + \text{recall}}$$

where:

$$\text{precision} = \frac{TP}{TP + FP}, \quad \text{recall} = \frac{TP}{TP + FN}$$

In "macro" F1, a separate F1 score is calculated for each `open_channels` value and then averaged.

## Submission Format

For each time value in the test set, you must predict `open_channels`. The file must have a header:

```
time,open_channels
500.0000,0
500.0001,2
...
```

## Dataset Description

In this competition, you will be predicting the number of open channels present, based on electrophysiological signal data.

**IMPORTANT**: While the time series appears continuous, the data is from discrete batches of 50 seconds long 10 kHz samples (500,000 rows per batch). The data from 0.0001-50.0000 is a different batch than 50.0001-100.0000, and thus discontinuous between 50.0000 and 50.0001.

## Files

- `train.csv`: Training set
- `test.csv`: Test set
- `sample_submission.csv`: Sample submission in correct format
