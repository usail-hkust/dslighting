# ScienceBench Task 12

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering, Deep Learning
- Source: kexinhuang12345/DeepPurpose
- Output Type: Text

## Task

Train a drug–target interaction model on the DAVIS benchmark to predict binding affinity between small-molecule drugs and protein targets. Fine-tune the model on the provided training/validation splits, score the antiviral candidates against the COVID-19 target sequence, rank the drugs by predicted affinity, and write the ordered SMILES strings to the required output file.

## Dataset

The `dti/` directory contains the DAVIS training/validation data plus the antiviral screening inputs:

- `DAVIS/affinity_train.csv`, `DAVIS/affinity_val.csv` – binding affinities used for training and validation.
- `DAVIS/drug_train.txt`, `DAVIS/drug_val.txt` – SMILES strings aligned with the affinity matrices.
- `DAVIS/target_seq.json` – protein target sequences.
- `antiviral_drugs.tab` – SMILES strings for antiviral candidates to rank.
- `covid_seq.txt` – amino-acid sequence for the COVID-19 target.

## Submission Format

Create submission with two columns: `gold_top5` and `removed_drugs`. Populate `gold_top5` with your ranked SMILES strings (highest affinity first) and list any filtered or disqualified drugs in the `removed_drugs` column (leave blank if none). Follow the structure shown in the public `sample_submission.csv`.

## Evaluation

Submissions are accepted when the ranked list omits the five disqualified drugs and the top five entries exactly match the reference antiviral ordering used by the original evaluation script.
