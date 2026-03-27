"""
Prepare fingerprint similarity visualization task.

This task requires analyzing protein-ligand interaction fingerprints and visualizing similarities.
"""

import shutil
from pathlib import Path


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the fingerprint similarity visualization task.

    Args:
        raw: Path to raw data directory
        public: Path to public data directory (visible to agents)
        private: Path to private data directory (for grading)
    """
    # Source paths from ScienceAgent-bench
    source_data_dir = raw / "ligand_protein"
    source_gold_result = raw / "ligand_similarity_gold.png"

    # Create directories
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy trajectory data to public directory
    for filename in ["top.pdb", "traj.xtc"]:
        source_file = source_data_dir / filename
        if source_file.exists():
            shutil.copy2(source_file, public / filename)
            print(f"Copied {filename} to {public / filename}")
        else:
            raise FileNotFoundError(f"Data file not found: {source_file}")

    # Create a simple sample submission (placeholder PNG)
    sample_submission_path = public / "sample_submission.png"
    import numpy as np
    from PIL import Image

    # Create a simple placeholder image
    placeholder = np.zeros((100, 100, 3), dtype=np.uint8)
    Image.fromarray(placeholder).save(sample_submission_path)
    print(f"Created sample submission at {sample_submission_path}")

    # Copy gold result to private directory
    if source_gold_result.exists():
        shutil.copy2(source_gold_result, private / "ligand_similarity_gold.png")
        print(f"Copied gold result to {private / 'ligand_similarity_gold.png'}")
    else:
        raise FileNotFoundError(f"Gold result not found: {source_gold_result}")

    print("Fingerprint similarity visualization task preparation complete")


if __name__ == "__main__":
    # For testing
    from pathlib import Path
    raw = Path("./raw")
    public = Path("./public")
    private = Path("./private")
    prepare(raw, public, private)
