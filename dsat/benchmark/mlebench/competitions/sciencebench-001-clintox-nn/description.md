# ScienceBench Task 1

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Feature Engineering, Deep Learning
- Source: deepchem/deepchem
- Output Type: Tabular

## Task

Train a multitask model on the Clintox dataset to predict a drug's toxicity and FDA approval status. Save the test set predictions, including the SMILES representation of drugs and the probability of positive labels.

## Dataset

[START Preview of clintox/clintox_train.csv]
smiles,FDA_APPROVED,CT_TOX
CCC(/C=C/Cl)(C#C)O,1,0
C[C@H]1C[C@H]2[C@@H]3CC[C@@H]([C@]3(C[C@@H]([C@@H]2[C@@]4(C1=CC(=O)CC4)C)O)C)C(=O)C,1,0
C[C@@H]1CCN([C@H](C1)C(=O)[O-])C(=O)[C@H](CCC[NH+]=C(N)N)NS(=O)(=O)c2cccc3c2NC[C@@H](C3)C,1,0
...
[END Preview of clintox/clintox_train.csv]

## Submission Format

Submit `sample_submission.csv` with the same header and column order as the template. Ensure numeric columns retain their dtype and identifiers remain aligned.

## Evaluation

Classification accuracy (higher is better).
