# Feedback Prize - English Language Learning

## Description

The goal of this competition is to assess the language proficiency of 8th-12th grade English Language Learners (ELLs). Utilizing a dataset of essays written by ELLs will help to develop proficiency models that better support all students. Your work will help ELLs receive more accurate feedback on their language development and expedite the grading cycle for teachers.

## Evaluation

Submissions are scored using MCRMSE, mean columnwise root mean squared error:

$$\textrm{MCRMSE} = \frac{1}{N_{t}}\sum_{j=1}^{N_{t}}\sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_{ij} - \hat{y}_{ij})^2}$$

where $N_t$ is the number of scored ground truth target columns (6 in this case), and $y$ and $\hat{y}$ are the actual and predicted values, respectively.

## Submission Format

For each text_id in the test set, you must predict a value for each of the six analytic measures. The file should contain a header and have the following format:

```
text_id,cohesion,syntax,vocabulary,phraseology,grammar,conventions
0000C359D63E,3.0,3.0,3.0,3.0,3.0,3.0
000BAD50D026,3.0,3.0,3.0,3.0,3.0,3.0
...
```

## Dataset Description

The dataset (ELLIPSE corpus) comprises argumentative essays written by 8th-12th grade English Language Learners (ELLs). The essays have been scored according to six analytic measures:

- **cohesion**: How well ideas are connected and flow together
- **syntax**: Sentence structure complexity and variety
- **vocabulary**: Range and appropriateness of word choice
- **phraseology**: Use of phrases and expressions
- **grammar**: Grammatical accuracy
- **conventions**: Spelling, punctuation, and formatting

Each measure represents a component of proficiency in essay writing, with greater scores corresponding to greater proficiency. The scores range from 1.0 to 5.0 in increments of 0.5.

## Files

- `train.csv`: Training set with full_text and scores for all six measures
- `test.csv`: Test set with full_text only
- `sample_submission.csv`: Sample submission in the correct format
