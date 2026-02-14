# Initial Data Scan: Tennis Match Flow and Performance Analysis



--- COMPREHENSIVE DATA REPORT ---

## Directory Structure (Current Working Directory)
```text
./
├── Wimbledon_featured_matches.csv
├── data_dictionary.csv
└── sampleSubmission.csv
```

## Data Schema Analysis
### Analysis of `data_dictionary.csv`

```text
            Data Type  Missing (%)  Cardinality                             Sample Values
variables      object          0.0           46                   ['match_id', 'player1']
explanation    object          0.0           46  ['match identification', 'first and l...
example        object          0.0           24  ['2023-wimbledon-1701 ("7" is the rou...
```

### Analysis of `sampleSubmission.csv`

```text
                   Data Type  Missing (%)  Cardinality                             Sample Values
match_id              object          0.0            1  ['2023-wimbledon-1301', '2023-wimbled...
player1               object          0.0            1      ['Carlos Alcaraz', 'Carlos Alcaraz']
player2               object          0.0            1        ['Nicolas Jarry', 'Nicolas Jarry']
elapsed_time          object          0.0            5                  ['00:00:00', '00:00:38']
set_no                 int64          0.0            1                                    [1, 1]
game_no                int64          0.0            1                                    [1, 1]
point_no               int64          0.0            5                                    [1, 2]
p1_sets                int64          0.0            1                                    [0, 0]
p2_sets                int64          0.0            1                                    [0, 0]
p1_games               int64          0.0            1                                    [0, 0]
p2_games               int64          0.0            1                                    [0, 0]
p1_score               int64          0.0            3                                    [0, 0]
p2_score               int64          0.0            3                                   [0, 15]
server                 int64          0.0            1                                    [1, 1]
serve_no               int64          0.0            2                                    [2, 1]
point_victor           int64          0.0            2                                    [2, 1]
p1_points_won          int64          0.0            4                                    [0, 1]
p2_points_won          int64          0.0            2                                    [1, 1]
game_victor            int64          0.0            1                                    [0, 0]
set_victor             int64          0.0            1                                    [0, 0]
p1_ace                 int64          0.0            2                                    [0, 0]
p2_ace                 int64          0.0            1                                    [0, 0]
p1_winner              int64          0.0            2                                    [0, 0]
p2_winner              int64          0.0            1                                    [0, 0]
winner_shot_type      object          0.0            2                                ['0', '0']
p1_double_fault        int64          0.0            1                                    [0, 0]
p2_double_fault        int64          0.0            1                                    [0, 0]
p1_unf_err             int64          0.0            2                                    [1, 0]
p2_unf_err             int64          0.0            1                                    [0, 0]
p1_net_pt              int64          0.0            1                                    [0, 0]
p2_net_pt              int64          0.0            2                                    [0, 0]
p1_net_pt_won          int64          0.0            1                                    [0, 0]
p2_net_pt_won          int64          0.0            1                                    [0, 0]
p1_break_pt            int64          0.0            1                                    [0, 0]
p2_break_pt            int64          0.0            1                                    [0, 0]
p1_break_pt_won        int64          0.0            1                                    [0, 0]
p2_break_pt_won        int64          0.0            1                                    [0, 0]
p1_break_pt_missed     int64          0.0            1                                    [0, 0]
p2_break_pt_missed     int64          0.0            1                                    [0, 0]
p1_distance_run      float64          0.0            5                              [6.0, 5.253]
p2_distance_run      float64          0.0            5                             [7.84, 7.094]
rally_count            int64          0.0            4                                    [2, 1]
speed_mph              int64          0.0            5                                 [95, 118]
serve_width           object          0.0            4                               ['BC', 'B']
serve_depth           object          0.0            2                           ['NCTL', 'CTL']
return_depth          object         20.0            2                              ['ND', 'ND']
```

