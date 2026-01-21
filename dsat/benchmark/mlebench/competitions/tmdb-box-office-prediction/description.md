# TMDB Box Office Prediction

## Description

In this competition, you're presented with metadata on over 7,000 past films from The Movie Database to try and predict their overall worldwide box office revenue. Data points provided include cast, crew, plot keywords, budget, posters, release dates, languages, production companies, and countries.

In a world where movies made an estimated $41.7 billion in 2018, the film industry is more popular than ever. But what movies make the most money at the box office? How much does a director matter? Or the budget?

## Evaluation

It is your job to predict the international box office revenue for each movie. For each id in the test set, you must predict the value of the revenue variable.

Submissions are evaluated on Root-Mean-Squared-Logarithmic-Error (RMSLE) between the predicted value and the actual revenue:

$$\text{RMSLE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (\log(p_i + 1) - \log(a_i + 1))^2}$$

where:
- $n$ is the number of movies in the test set
- $p_i$ is your predicted revenue
- $a_i$ is the actual revenue
- $\log(x)$ is the natural logarithm

Logs are taken to not overweight blockbuster revenue movies.

## Submission Format

The file should contain a header and have the following format:

```
id,revenue
1461,1000000
1462,50000
1463,800000000
...
```

## Dataset Description

In this dataset, you are provided with 7,398 movies and a variety of metadata obtained from The Movie Database (TMDB). Movies are labeled with id. Data points include cast, crew, plot keywords, budget, posters, release dates, languages, production companies, and countries.

**Note**: Many movies are remade over the years, therefore it may seem like multiple instances of a movie may appear in the data. However, they are different and should be considered separate movies. In addition, some movies may share a title but be entirely unrelated.

## Files

- `train.csv`: Training data with movie metadata and revenue
- `test.csv`: Test data with movie metadata only
- `sample_submission.csv`: Sample submission in the correct format
