"""
Prepare EEG processing visualization task.

This task requires processing EEG data and generating a visualization of frequency band power.
"""

import shutil
from pathlib import Path


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the EEG processing task.

    Args:
        raw: Path to raw data directory
        public: Path to public data directory (visible to agents)
        private: Path to private data directory (for grading)
    """
    # Source paths from ScienceAgent-bench
    source_data_dir = raw / "eeg_processing"
    source_gold_result = raw / "biopsykit_eeg_processing_vis1_gold.png"

    # Create directories
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy EEG data to public directory
    eeg_data_file = source_data_dir / "eeg_muse_example.csv"
    if eeg_data_file.exists():
        shutil.copy2(eeg_data_file, public / "eeg_muse_example.csv")
        print(f"Copied EEG data to {public / 'eeg_muse_example.csv'}")
    else:
        raise FileNotFoundError(f"EEG data file not found: {eeg_data_file}")

    # Create a simple sample submission (placeholder PNG)
    sample_submission_path = public / "sample_submission.png"
    # Create a minimal 1x1 PNG as placeholder
    import numpy as np
    from PIL import Image

    # Create a simple placeholder image
    placeholder = np.zeros((100, 100, 3), dtype=np.uint8)
    Image.fromarray(placeholder).save(sample_submission_path)
    print(f"Created sample submission at {sample_submission_path}")

    # Copy gold result to private directory
    if source_gold_result.exists():
        shutil.copy2(source_gold_result, private / "biopsykit_eeg_processing_vis1_gold.png")
        print(f"Copied gold result to {private / 'biopsykit_eeg_processing_vis1_gold.png'}")
    else:
        raise FileNotFoundError(f"Gold result not found: {source_gold_result}")

    print("EEG processing task preparation complete")


if __name__ == "__main__":
    # For testing
    from pathlib import Path
    raw = Path("./raw")
    public = Path("./public")
    private = Path("./private")
    prepare(raw, public, private)
