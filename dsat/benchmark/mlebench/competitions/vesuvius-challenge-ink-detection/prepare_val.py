import shutil
from pathlib import Path
from typing import List

import pandas as pd
from PIL import Image
from tqdm import tqdm

from mlebench.utils import read_csv


def prepare(raw: Path, public: Path, private: Path) -> None:
    """
    Prepares the data by creating a primary train/test split and a secondary
    train/validation split.

    The primary split uses fragments {1, 2} for training and {3} for testing,
    outputting to `public/` and `private/` directories.

    The secondary split uses fragment {1} for training and {2} for validation,
    outputting to `public_val/` and `private_val/` directories, mirroring the
    structure and logic of the primary split.
    """

    def _create_split_data(
        train_fragment_ids: List[str],
        test_fragment_id: str,
        raw_path: Path,
        public_path: Path,
        private_path: Path,
    ) -> None:
        """
        A generic helper function to process a set of train/test fragments
        and generate the corresponding public and private data.
        """
        # Ensure destination directories exist
        public_path.mkdir(parents=True, exist_ok=True)
        private_path.mkdir(parents=True, exist_ok=True)

        # Copy train images to `public_path/train/{id}/`
        for frag_id in train_fragment_ids:
            shutil.copytree(
                src=raw_path / "train" / frag_id,
                dst=public_path / "train" / frag_id,
                dirs_exist_ok=True,  # Make script re-runnable
            )

        test_fragment_path = raw_path / "train" / test_fragment_id

        # Create test `inklabels_rle.csv`
        inklabels_rle = read_csv(test_fragment_path / "inklabels_rle.csv")

        assert (
            len(inklabels_rle) == 1
        ), f"Expected a single row in `inklabels_rle.csv`, got {len(inklabels_rle)} rows."

        img_path = test_fragment_path / "ir.png"

        assert img_path.is_file(), f"Expected image file at {img_path}, but it does not exist."

        with Image.open(img_path) as img:
            width, height = img.size

        inklabels_rle["width"] = width
        inklabels_rle["height"] = height
        inklabels_rle["Id"] = "a"

        inklabels_rle.to_csv(private_path / "inklabels_rle.csv", index=False)

        # Write `gold_submission.csv`
        inklabels_rle.drop(columns=["width", "height"]).to_csv(
            private_path / "gold_submission.csv",
            index=False,
        )

        # Copy test images to `public_path/test/a/`
        test_imgs = list(test_fragment_path.rglob("*"))

        for fpath in tqdm(test_imgs, desc=f"Creating test images for {public_path.name}"):
            if not fpath.is_file():
                continue

            assert fpath.suffix in [
                ".png",
                ".csv",
                ".tif",
            ], f"Expected file with extension png, csv, or tif, got `{fpath.suffix}` for file `{fpath}`"

            relative_path = fpath.relative_to(test_fragment_path)

            if fpath.name in ["inklabels.png", "inklabels_rle.csv", "ir.png"]:
                continue  # skip test images and labels

            dst = public_path / "test" / "a" / relative_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(fpath, dst)  # everything else to `public_path`

        sample_submission = pd.DataFrame({"Id": ["a"], "Predicted": ["1 1 5 1"]})
        sample_submission.to_csv(public_path / "sample_submission.csv", index=False)

        # Sanity checks
        assert len(sample_submission) == len(inklabels_rle), (
            f"Expected {len(inklabels_rle)} rows in `sample_submission.csv`, got "
            f"{len(sample_submission)} rows."
        )

        actual_sample_submission = read_csv(public_path / "sample_submission.csv")
        actual_inklabels_rle = read_csv(private_path / "inklabels_rle.csv")

        assert (
            "Id" in actual_sample_submission.columns
        ), f"Expected column `Id` in `sample_submission.csv`."
        assert (
            "Predicted" in actual_sample_submission.columns
        ), f"Expected column `Predicted` in `sample_submission.csv`."

        assert "Id" in actual_inklabels_rle.columns, f"Expected column `Id` in `inklabels_rle.csv`."
        assert (
            "Predicted" in actual_inklabels_rle.columns
        ), f"Expected column `Predicted` in `inklabels_rle.csv`."
        assert (
            "width" in actual_inklabels_rle.columns
        ), f"Expected column `width` in `inklabels_rle.csv`."
        assert (
            "height" in actual_inklabels_rle.columns
        ), f"Expected column `height` in `inklabels_rle.csv`."

        for frag_id in train_fragment_ids:
            assert len(list((public_path / "train" / frag_id).rglob("*"))) == len(
                list((raw_path / "train" / frag_id).rglob("*"))
            ), (
                f"Expected {len(list((raw_path / 'train' / frag_id).rglob('*')))} files in `{public_path}/train/{frag_id}`, got "
                f"{len(list((public_path / 'train' / frag_id).rglob('*')))} files."
            )

        n_test_actual = len(list((public_path / "test" / "a").rglob("*")))
        n_test_expected = len(list(test_fragment_path.rglob("*"))) - len(
            ["inklabels.png", "inklabels_rle.csv", "ir.png"]
        )

        assert n_test_actual == n_test_expected, (
            f"Expected " f"{n_test_expected} " f"files in `{public_path}/test/a`, got {n_test_actual} files."
        )

    # --- Primary Split (Original Behavior) ---
    # This call generates the original `public` and `private` directories.
    # The contents will be identical to the original script's output.
    _create_split_data(
        train_fragment_ids=["1", "2"],
        test_fragment_id="3",
        raw_path=raw,
        public_path=public,
        private_path=private,
    )

    # --- New Validation Split ---
    # Define paths for the new validation set directories.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # This call splits the original training data ({1, 2}) into a new, smaller
    # training set ({1}) and a validation set ({2}). The output structure
    # in `public_val` and `private_val` will mirror the original one.
    _create_split_data(
        train_fragment_ids=["1"],
        test_fragment_id="2",
        raw_path=raw,
        public_path=public_val,
        private_path=private_val,
    )