# Santander Customer Satisfaction

## Task Description

Predict whether a Santander Bank customer is dissatisfied based on hundreds of anonymized account-level features. The binary target `TARGET` equals `1` when the customer is unhappy and `0` otherwise. A good model lets the bank intervene and retain customers before they churn.

## Data Description

- **train.csv** – labelled training set with columns `ID`, `TARGET`, and the anonymized feature set.
- **test.csv** – public test features without the `TARGET` label.
- **sample_submission.csv** – reference submission template containing the required `ID,TARGET` header and ordering.
- **gold_submission.csv** – ground-truth probabilities for private evaluation (kept hidden from participants).

All files are provided in CSV format. Feature names follow the original Kaggle competition naming convention (e.g. `var3`, `ind_var5`, `num_var37`).

## Evaluation

Submissions are scored with the area under the receiver operating characteristic curve (AUC-ROC) between the predicted probability and the true `TARGET`. Higher values are better, with `1.0` indicating a perfect ranking.

## Submission Format

Participants must upload a CSV with two columns:

```text
ID,TARGET
2,0.135
5,0.042
6,0.873
```

- `ID` must exactly match the identifiers in the public test set.
- `TARGET` should be the predicted probability that the corresponding customer is dissatisfied (`TARGET = 1`).

## Source

Original competition: [Santander Customer Satisfaction](https://www.kaggle.com/competitions/santander-customer-satisfaction). Data is redistributed under Kaggle’s terms for educational benchmarking.
