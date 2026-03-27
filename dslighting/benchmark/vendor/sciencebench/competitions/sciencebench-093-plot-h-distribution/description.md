# ScienceBench Task 93: plot_h_distribution

## Overview

- **Domain**: Psychology and Cognitive Science
- **Subtask Categories**: Data Visualization
- **Source**: brand-d/cogsci-jnmf
- **Output Type**: Image (PNG)

## Task

Using the given matrix data in `fit_result_conscientiousness_H_low.npy` and `fit_result_conscientiousness_H_high.npy`, plot the data distributions.

Create three subplots showing:
1. **High split**: Values from the second column of H_high
2. **Common split**: Concatenation of values from the first column of H_high and H_low
3. **Low split**: Values from the second column of H_low

All values should be rescaled such that the largest value among all is 1.0.

## Input/Output

**Input Files**:
- `fit_result_conscientiousness_H_high.npy`: High split matrix data
- `fit_result_conscientiousness_H_low.npy`: Low split matrix data

**Output Format**:
- Format: PNG image
- Layout: Three subplots arranged horizontally (left to right: High, Common, Low)

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
