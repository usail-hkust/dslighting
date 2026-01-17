import numpy as np
import pandas as pd
from pathlib import Path


def _label_sort_key(label: str):
    try:
        return float(label)
    except (TypeError, ValueError):
        return label


def _build_label_mapping(raw_labels):
    unique_labels = sorted({lbl for lbl in raw_labels if lbl is not None}, key=_label_sort_key)
    return {label: idx for idx, label in enumerate(unique_labels)}


def _load_ts_split(ts_path: Path, label_mapping=None):
    """
    Load a .ts file into a dense NumPy tensor and label vector.

    Returns:
        data: np.ndarray of shape (num_samples, seq_len, num_features)
        labels: np.ndarray of int labels with shape (num_samples,)
        mapping: dict mapping original labels to encoded integers
    """
    num_dimensions = None
    seq_length_hint = None
    in_data_section = False

    samples = []
    raw_labels = []

    with ts_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if not in_data_section:
                if stripped.lower().startswith("@data"):
                    in_data_section = True
                    continue

                if stripped.startswith("@"):
                    parts = stripped[1:].split(None, 1)
                    key = parts[0].lower()
                    value = parts[1].strip() if len(parts) > 1 else ""
                    if key == "dimensions":
                        num_dimensions = int(value)
                    elif key == "serieslength":
                        try:
                            seq_length_hint = int(value)
                        except ValueError:
                            seq_length_hint = None
                    continue

                continue

            # Data row
            if num_dimensions is None:
                raise ValueError(f"Unable to parse dimensions from header in {ts_path}")

            parts = stripped.split(":")
            if len(parts) < num_dimensions:
                raise ValueError(f"Unexpected data row format in {ts_path}: {stripped[:50]}...")

            dimension_series = []
            for dim_idx in range(num_dimensions):
                seq_str = parts[dim_idx].strip()
                if not seq_str:
                    dimension_series.append([])
                    continue

                values = []
                for token in seq_str.split(","):
                    token = token.strip()
                    if not token:
                        continue
                    if token == "?":
                        values.append(np.nan)
                    else:
                        values.append(float(token))

                dimension_series.append(values)

            samples.append(dimension_series)

            label_str = parts[num_dimensions].strip() if len(parts) > num_dimensions else None
            raw_labels.append(label_str or None)

    if not samples:
        raise ValueError(f"No samples parsed from {ts_path}")

    # Ensure label mapping
    mapping = label_mapping or _build_label_mapping(raw_labels)
    labels = np.array([mapping[label] for label in raw_labels], dtype=np.int64)

    # Convert dimension lists into dense arrays
    tensor_samples = []
    global_seq_len = None

    for dims in samples:
        series_arrays = []
        sample_len = None

        for dim_values in dims:
            arr = np.asarray(dim_values, dtype=np.float32)
            if sample_len is None:
                sample_len = arr.shape[0]
            elif arr.shape[0] != sample_len:
                raise ValueError("Inconsistent dimension lengths within sample.")

            if seq_length_hint is not None and arr.shape[0] != seq_length_hint:
                raise ValueError("Sequence length mismatch relative to header declaration.")

            series_arrays.append(arr)

        sample_tensor = np.stack(series_arrays, axis=-1)  # (seq_len, num_features)
        global_seq_len = sample_tensor.shape[0] if global_seq_len is None else global_seq_len
        if sample_tensor.shape[0] != global_seq_len:
            raise ValueError("Inconsistent sequence lengths across samples.")

        tensor_samples.append(sample_tensor)

    data = np.stack(tensor_samples, axis=0)  # (num_samples, seq_len, num_features)
    return data, labels, mapping


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the handwriting dataset for the benchmark.

    Args:
        raw: Path to raw data directory (contains Handwriting_TRAIN.ts and Handwriting_TEST.ts)
        public: Path to public directory (visible to participants)
        private: Path to private directory (hidden from participants, used for grading)
    """
    # Materialize dense tensors from the raw .ts files
    train_path = raw / "Handwriting_TRAIN.ts"
    test_path = raw / "Handwriting_TEST.ts"

    X_train, y_train, label_mapping = _load_ts_split(train_path)
    X_test, y_test, _ = _load_ts_split(test_path, label_mapping=label_mapping)

    # Convert labels to 1D arrays
    y_train = np.asarray(y_train, dtype=np.int64).reshape(-1)
    y_test = np.asarray(y_test, dtype=np.int64).reshape(-1)

    # Persist prepared arrays for participants
    np.save(public / "train_data.npy", X_train)
    np.save(public / "train_labels.npy", y_train)
    np.save(public / "test_data.npy", X_test)

    # Sample submission (default all zeros)
    sample_submission = pd.DataFrame({"id": range(len(y_test)), "label": 0})
    sample_submission.to_csv(public / "sample_submission.csv", index=False)

    # Private ground-truth labels for grading
    test_labels_df = pd.DataFrame({"id": range(len(y_test)), "label": y_test})
    test_labels_df.to_csv(private / "test_labels.csv", index=False)

    # Basic validation checks
    expected_public = [
        public / "train_data.npy",
        public / "train_labels.npy",
        public / "test_data.npy",
        public / "sample_submission.csv",
    ]
    for path in expected_public:
        assert path.exists(), f"Missing public artifact: {path.name}"

    assert (private / "test_labels.csv").exists(), "Test labels should exist"

    print(
        "Prepared handwriting dataset:\n"
        f"  - Train split: {X_train.shape}, labels: {y_train.shape}\n"
        f"  - Test split: {X_test.shape}, labels: {y_test.shape}"
    )
