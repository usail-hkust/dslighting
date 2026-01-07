# Quickstart Guide

Start in 30 seconds; customize your first data science benchmark in 5 minutes.

---

## 🚀 30-second run

```bash
cd examples/custom_benchmark/en
bash run_example.sh
```

**Automatically does**:
1. ✓ Generate 100 synthetic house-price rows
2. ✓ Prepare train (80) / test (20) splits
3. ✓ Run the mock agent to create predictions
4. ✓ Compute the RMSE score

**Result**: `test_results/` contains the submission file and score

---

## 📖 5-minute structure tour

### Directory at a glance

```
custom_benchmark/en/
├── competitions/           # Competition registry
│   └── custom_house_price_prediction/
│       ├── config.yaml            # Task ID, grader, etc.
│       ├── description.md         # Task description
│       ├── grade.py               # Scoring logic (RMSE)
│       └── prepare.py             # Data prep (train/test split)
│
└── data/                   # Dataset
    └── custom-house-price-prediction/
        ├── raw/houses.csv         # Raw data
        └── prepared/
            ├── public/train.csv   # Train data (visible)
            └── private/answer.csv # Test answers (scoring)
```

### Three key concepts

| Concept | File | Purpose |
|------|------|------|
| **Register** | `competitions/*/config.yaml` | Define task metadata and pipeline |
| **Prepare** | `competitions/*/prepare.py` | Raw data → public/private splits |
| **Score** | `competitions/*/grade.py` | Submission → score |

---

## 🔧 5-minute customization

### Step 1: Tweak data generation

Edit `prepare_example_data.py`:

```python
# More samples
df = generate_house_data(n_samples=500)  # from 100 → 500

# Add features
data['bathrooms'] = np.random.randint(1, 4, n_samples)
data['garage'] = np.random.choice([0, 1, 2], n_samples)
```

### Step 2: Adjust the grader

Edit `competitions/custom_house_price_prediction/grade.py`:

```python
# Switch from RMSE to MAE
def grade(submission, answers):
    mae = np.mean(np.abs(submission['predicted_price'] - answers['actual_price']))
    return mae
```

### Step 3: Update the task description

Edit `competitions/custom_house_price_prediction/description.md`:

```markdown
## New features
- bathrooms: number of bathrooms (1-3)
- garage: number of garages (0-2)

## Metric
MAE (Mean Absolute Error) - lower is better
```

### Step 4: Regenerate and test

```bash
# 1. Regenerate data
python prepare_example_data.py

# 2. Re-run preparation
cd competitions/custom_house_price_prediction
python prepare.py
cd ../..

# 3. Test
python custom_benchmark.py
```

---

## 🏗️ Create a new task

### Template: classification example

```bash
# 1. Create directories
mkdir -p competitions/my-classification-task
mkdir -p data/my-classification-task/raw

# 2. Create config.yaml
cat > competitions/my-classification-task/config.yaml << EOF
id: my-classification-task
name: My Classification Challenge
competition_type: kaggle
grader:
  name: accuracy
  grade_fn: competitions.my-classification-task.grade:grade
preparer: competitions.my-classification-task.prepare:prepare
EOF

# 3. Create grade.py
cat > competitions/my-classification-task/grade.py << 'EOF'
import pandas as pd

def grade(submission, answers):
    accuracy = (submission['predicted'] == answers['actual']).mean()
    return accuracy
EOF
```

### Full template

Use `competitions/custom_house_price_prediction/` as a reference, copy and modify:
- `config.yaml` - update ID and name
- `description.md` - describe the task
- `prepare.py` - implement data prep
- `grade.py` - implement scoring

---

## 🔗 Integrate with the main framework

### Option A: Standalone run (good for testing)

```bash
python custom_benchmark.py
```

### Option B: Wire into `run_benchmark.py`

1. Edit `run_benchmark.py`:
```python
from examples.custom_benchmark.custom_benchmark import HousePriceBenchmark

BENCHMARK_CLASSES = {
    "mle": MLEBenchmark,
    "house_price": HousePriceBenchmark,  # add
}
```

2. Run:
```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark house_price \
  --log-path ./runs/house_price_results
```

---

## 📊 View results

### Score output

```bash
✓ RMSE: 25432.18
```

### Result CSV

```csv
task_id,submission_path,rmse_score,cost,submission_valid,error_message
custom-house-price-prediction,./test_results/submission_xxx.csv,25432.18,0.0,True,
```

### Submission file

```csv
house_id,predicted_price
81,287534.12
82,345123.45
...
```

---

## ⚡ Common commands

```bash
# Full flow
bash run_example.sh

# Generate only
python prepare_example_data.py

# Prepare dataset only
cd competitions/custom_house_price_prediction && python prepare.py

# Test benchmark
python custom_benchmark.py

# Test grader
cd competitions/custom_house_price_prediction && python grade.py
```

---

## 🐛 Troubleshooting

### Problem: "competition data directory does not exist"

**Fix**:
```bash
python prepare_example_data.py
cd competitions/custom_house_price_prediction
python prepare.py
```

### Problem: "grading failed"

**Check**:
1. Submission file exists
2. Column names are `house_id`, `predicted_price`
3. `house_id` matches the test set

**Debug**:
```bash
python -c "
import pandas as pd
sub = pd.read_csv('test_results/submission_xxx.csv')
ans = pd.read_csv('data/custom-house-price-prediction/prepared/private/answer.csv')
print('Submission columns:', sub.columns.tolist())
print('Answer columns:', ans.columns.tolist())
print('Submission shape:', sub.shape)
print('Answer shape:', ans.shape)
"
```

---

## 📚 Next steps

- 📖 Read [README.md](README.md) for structure details
- 🔍 Inspect files under `competitions/*/` for implementations
- 🚀 Check `dsat/benchmark/mle.py` for production-ready code
- 💡 Build and share your own task!

---

**Tip**: Problems? Check the logs or run `python grade.py` to test the grader.
