# ScienceBench Task 78

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering, Deep Learning
- Source: deepchem/deepchem
- Expected Output: pucci-proteins_test_pred.csv
- Output Type: Tabular

## Task

Train a neural network model using the pucci dataset to predict the melting temperature (deltaTm) of proteins caused due to the point mutation of one amino acid at chain A. The dataset also contains the PDB files which need to be processed to retrieve the original (wild-type) amino acid sequence and then to create the mutated sequences. Save the predictions for the test set as a single column dataframe "deltaTm" to the file "output file".

## Dataset

[START Dataset Preview: pucci]
|-- pucci-proteins_train.csv
|-- pucci-proteins_test.csv
|-- PDBs/1aky.pdb
|-- PDBs/1azp.pdb
[END Dataset Preview]

## Submission Format

Submit `sample_submission.csv` with the same header and column order as the template. The file uses:

- `test_data_id`: row identifier
- `deltaTm`: predicted value

## Evaluation

The grader computes the mean absolute error (MAE) against the reference labels.
