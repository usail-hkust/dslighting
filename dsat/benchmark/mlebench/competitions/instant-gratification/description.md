# Instant Gratification

## Description

This is a synchronous Kernels-only competition introducing Kaggle's new format. When you submit from a Kernel, Kaggle will run the code against both the public and private test sets in real time, providing instant feedback on whether your code runs successfully.

This competition presents an anonymized, binary classification dataset. While it may feel like a normal KO competition, there are new mechanics in play with truly withheld test sets and real-time validation.

## Evaluation

Submissions are evaluated on **area under the ROC curve** between the predicted probability and the observed target.

## Submission Format

For each id in the test set, you must predict a probability for the target variable:

```
id,target
ba88c155ba898fc8b5099893036ef205,0.5
7cbab5cea99169139e7e6d8ff74ebb77,0.5
...
```

## Dataset Description

This is an anonymized, binary classification dataset. There was no data dictionary, but this poem was handwritten:

*Silly column names abound,
but the test set is a mystery.
Careful how you pick and slice,
or be left behind by history.*

## Files

- `train.csv`: Training set
- `test.csv`: Test set
- `sample_submission.csv`: Sample submission in correct format
