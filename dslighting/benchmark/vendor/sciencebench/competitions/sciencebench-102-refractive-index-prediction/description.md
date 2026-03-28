# ScienceBench Task 102: refractive_index_prediction

- Domain: Computational Chemistry
- Subtask Categories: Deep Learning
- Source: ppdebreuck/modnet
- Output Type: CSV

## Task

Train a MODNet regressor on the provided refractive-index dataset and predict the refractive index for the held-out materials.

## Dataset

[START Dataset Preview: ref_index]
|-- md_ref_index_train
|-- MP_2018.6
[END Dataset Preview]

## Submission Format

Save predictions as a CSV file with a `refractive_index` column aligned to the test set order.

## Evaluation

The grader computes the mean absolute error against the gold targets (pass if MAE < 0.78).
