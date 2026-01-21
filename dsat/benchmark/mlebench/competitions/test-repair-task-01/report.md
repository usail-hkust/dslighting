# Report: Bike Sharing Demand Prediction



--- COMPREHENSIVE DATA REPORT ---

## Directory Structure (Current Working Directory)
```text
./
├── sample.csv
└── test.csv
```

## Data Schema Analysis
### Analysis of `sample.csv`

```text
           Data Type  Missing (%)  Cardinality                             Sample Values
datetime      object          0.0            5  ['2011-07-06 05:00:00', '2012-08-04 1...
season         int64          0.0            3                                    [3, 3]
holiday        int64          0.0            1                                    [0, 0]
workingday     int64          0.0            2                                    [1, 0]
weather        int64          0.0            2                                    [1, 1]
temp         float64          0.0            5                             [27.88, 36.9]
atemp        float64          0.0            5                            [31.82, 40.91]
humidity       int64          0.0            5                                  [83, 39]
windspeed    float64          0.0            4                         [6.0032, 19.9995]
casual         int64          0.0            1                                    [0, 0]
registered     int64          0.0            1                                    [0, 0]
count          int64          0.0            1                                    [0, 0]
```

### Analysis of `test.csv`

```text
           Data Type  Missing (%)  Cardinality                             Sample Values
datetime      object          0.0            5  ['2011-07-06 05:00:00', '2012-08-04 1...
season         int64          0.0            3                                    [3, 3]
holiday        int64          0.0            1                                    [0, 0]
workingday     int64          0.0            2                                    [1, 0]
weather        int64          0.0            2                                    [1, 1]
temp         float64          0.0            5                             [27.88, 36.9]
atemp        float64          0.0            5                            [31.82, 40.91]
humidity       int64          0.0            5                                  [83, 39]
windspeed    float64          0.0            4                         [6.0032, 19.9995]
```

