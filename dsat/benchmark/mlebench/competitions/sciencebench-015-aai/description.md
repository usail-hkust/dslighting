# ScienceBench Task 15

## Overview

- Domain: Bioinformatics
- Subtask Categories: Deep Learning
- Source: swansonk14/admet_ai
- Expected Output: aai_preds.csv
- Output Type: Tabular

## Task

Train a model on the ames dataset to predict a drug's toxicity. Save the test set predictions, including the SMILES representaion of drugs and the probability of being positive, to "output file".

## Dataset

[START Preview of ames/train.csv]
,Drug_ID,Drug,Y
0,Drug 2589,c1ccc2cnccc2c1,0
1,Drug 2217,Nc1c2ncn(Cc3ccccc3)c2nc[n+]1[O-],1
2,Drug 5485,CC1=CC(=C(C#N)C#N)C=C(/C=C/c2ccc(N(C)C)cc2)O1,1
...
[END Preview of ames/train.csv]

## Submission Format

Submit `sample_submission.csv` with the same header and column order as the template. Ensure numeric columns retain their dtype and identifiers remain aligned.

## Evaluation

Classification accuracy (higher is better).
