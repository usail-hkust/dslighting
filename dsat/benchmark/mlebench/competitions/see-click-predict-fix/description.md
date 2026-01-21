# See Click Predict Fix

## Description

This competition aims to quantify and predict how people will react to specific 311 issues. What makes an issue urgent? What do citizens really care about? The data set contains several hundred thousand 311 issues from four cities.

311 is a mechanism where citizens can express their desire to solve a problem by submitting a description of what needs to be done. Citizens can vote and comment on issues so government officials understand priorities.

## Evaluation

Your model should predict, for each issue, the number of views, votes, and comments. We use the **Root Mean Squared Logarithmic Error (RMSLE)** across all three targets:

$$\text{RMSLE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (\log(p_i + 1) - \log(a_i + 1))^2}$$

where n is three times the total number of issues (summing over views, votes, and comments).

## Submission Format

```
id,num_views,num_votes,num_comments
343272,0,0,0
274860,0,0,0
...
```

## Dataset Description

You are provided with 311 issues from four cities since 2012. The goal is to predict the number of views, votes, and comments each issue has received.

## Data Fields

- `id`: randomly assigned id
- `latitude`, `longitude`: location of the issue
- `summary`: short text title
- `description`: longer text explanation
- `num_votes`: number of user-generated votes (target)
- `num_comments`: number of user-generated comments (target)
- `num_views`: number of views (target)
- `source`: categorical variable indicating where the issue was created
- `created_time`: when the issue originated
- `tag_type`: categorical variable of issue type

## Files

- `train.csv`: Training data with target variables
- `test.csv`: Test data without target variables
- `sample_submission.csv`: Sample submission in correct format
