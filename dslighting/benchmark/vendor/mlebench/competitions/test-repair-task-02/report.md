# Report: Bike Sharing Demand Prediction



--- COMPREHENSIVE DATA REPORT ---

## Directory Structure (Current Working Directory)
```text
./
├── sample.csv
├── test.csv
└── train.csv
```

## Data Schema Analysis
### Analysis of `sample.csv`

```text
           Data Type  Missing (%)  Cardinality                             Sample Values
datetime      object          0.0         1742  ['2011-12-02 13:00:00', '2012-04-18 2...
casual         int64          0.0            1                                  [36, 36]
registered     int64          0.0            1                                [156, 156]
count          int64          0.0            1                                [192, 192]
```

### Analysis of `test.csv`

```text
           Data Type  Missing (%)  Cardinality                             Sample Values
datetime      object          0.0         1742  ['2011-12-02 13:00:00', '2012-04-18 2...
season         int64          0.0            4                                    [4, 2]
holiday        int64          0.0            2                                    [0, 0]
workingday     int64          0.0            2                                    [1, 1]
weather        int64          0.0            3                                    [1, 2]
temp         float64          0.0           46                             [16.4, 17.22]
atemp        float64          0.0           55                           [20.455, 21.21]
humidity       int64          0.0           77                                  [47, 77]
windspeed    float64          0.0           25                          [8.9981, 6.0032]
```

### Analysis of `train.csv`

```text
           Data Type  Missing (%)  Cardinality                             Sample Values
datetime      object          0.0         5000  ['2011-03-11 21:00:00', '2012-07-01 1...
season         int64          0.0            4                                    [1, 3]
holiday        int64          0.0            2                                    [0, 0]
workingday     int64          0.0            2                                    [1, 0]
weather        int64          0.0            4                                    [2, 1]
temp         float64          0.0           48                             [12.3, 36.08]
atemp        float64          0.0           59                           [14.395, 40.15]
humidity       int64          0.0           88                                  [52, 39]
windspeed    float64          0.0           26                        [16.9979, 15.0013]
casual         int64          0.0          268                                 [10, 121]
registered     int64          0.0          633                                 [43, 256]
count          int64          0.0          718                                 [53, 377]
```

