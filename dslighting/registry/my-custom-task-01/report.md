# Report: Bike Sharing Demand Prediction



--- COMPREHENSIVE DATA REPORT ---

## Directory Structure (Current Working Directory)
```text
./
├── sample.csv
├── sampleSubmission.csv
├── test.csv
├── test_answer.csv
└── train.csv
```

## Data Schema Analysis
### Analysis of `sample.csv`

```text
         Data Type  Missing (%)  Cardinality                             Sample Values
datetime    object          0.0         2178  ['2011-07-19 11:00:00', '2012-01-16 0...
count        int64          0.0            1                                    [0, 0]
```

### Analysis of `sampleSubmission.csv`

```text
         Data Type  Missing (%)  Cardinality                             Sample Values
datetime    object          0.0         5000  ['2011-01-20 00:00:00', '2011-01-20 0...
count        int64          0.0            1                                    [0, 0]
```

### Analysis of `test.csv`

```text
           Data Type  Missing (%)  Cardinality                             Sample Values
datetime      object          0.0         2178  ['2011-07-19 11:00:00', '2012-01-16 0...
season         int64          0.0            4                                    [3, 1]
holiday        int64          0.0            2                                    [0, 1]
workingday     int64          0.0            2                                    [1, 0]
weather        int64          0.0            3                                    [1, 1]
temp         float64          0.0           47                              [33.62, 4.1]
atemp        float64          0.0           57                             [40.15, 6.82]
humidity       int64          0.0           80                                  [59, 54]
windspeed    float64          0.0           24                             [0.0, 6.0032]
```

### Analysis of `test_answer.csv`

```text
         Data Type  Missing (%)  Cardinality                             Sample Values
datetime    object          0.0         2178  ['2011-07-19 11:00:00', '2012-01-16 0...
count        int64          0.0          582                                 [127, 13]
```

### Analysis of `train.csv`

```text
           Data Type  Missing (%)  Cardinality                             Sample Values
datetime      object          0.0         5000  ['2011-07-06 05:00:00', '2012-08-04 1...
season         int64          0.0            4                                    [3, 3]
holiday        int64          0.0            2                                    [0, 0]
workingday     int64          0.0            2                                    [1, 0]
weather        int64          0.0            3                                    [1, 1]
temp         float64          0.0           48                             [27.88, 36.9]
atemp        float64          0.0           59                            [31.82, 40.91]
humidity       int64          0.0           82                                  [83, 39]
windspeed    float64          0.0           26                         [6.0032, 19.9995]
casual         int64          0.0          258                                  [5, 197]
registered     int64          0.0          625                                 [30, 253]
count          int64          0.0          715                                 [35, 450]
```

