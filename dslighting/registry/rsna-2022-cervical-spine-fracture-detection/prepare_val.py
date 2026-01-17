import random
import shutil
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from tqdm.auto import tqdm

from mlebench.utils import read_csv


def _split_and_save(
    source_train_df: pd.DataFrame,
    source_bbox_df: pd.DataFrame,
    source_seg_ids: List[str],
    raw_images_path: Path,
    raw_segmentations_path: Path,
    train_ratio: float,
    rng: random.Random,
    public_dir: Path,
    private_dir: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Performs a data split based on provided source data and saves the results.

    This function replicates the original script's logic for splitting data based on
    ratios of bounding boxes, segmentations, and their overlap. It then saves the
    resulting train/test sets, metadata, and copies image files to the specified
    public and private directories.

    Args:
        source_train_df: DataFrame with the main training metadata to be split.
        source_bbox_df: DataFrame with bounding box data to be split.
        source_seg_ids: List of StudyInstanceUIDs that have segmentations.
        raw_images_path: Path to the original directory of all study images.
        raw_segmentations_path: Path to the original directory of all segmentations.
        train_ratio: The ratio of the source data to be used for the new training set.
        rng: A random number generator instance for deterministic sampling.
        public_dir: The target public directory for outputs.
        private_dir: The target private directory for outputs.

    Returns:
        A tuple containing the data for the *training* portion of the split:
        (new_train_df, new_train_bboxes_df, new_segmentation_ids)
    """
    public_dir.mkdir(exist_ok=True, parents=True)
    private_dir.mkdir(exist_ok=True, parents=True)

    num_source_train = len(source_train_df)
    num_train_samples = round(num_source_train * train_ratio)

    # bboxes
    source_train_bbox_ids = sorted(source_bbox_df["StudyInstanceUID"].unique())
    source_num_train_bbox_ids = len(source_train_bbox_ids)
    new_num_train_bbox_ids = round(source_num_train_bbox_ids * train_ratio)

    # segmentations
    source_num_train_segmentation_ids = len(source_seg_ids)
    new_num_train_segmentation_ids = round(source_num_train_segmentation_ids * train_ratio)

    # overlap: list of StudyInstanceUIDs that have both bounding boxes and segmentations
    source_overlap_ids = [uid for uid in source_train_bbox_ids if uid in source_seg_ids]
    source_num_overlap = len(source_overlap_ids)
    new_num_overlap = round(source_num_overlap * train_ratio)

    # start populating new train by picking the overlap instances
    # sample new_num_overlap instances from the overlap randomly
    new_overlap_ids = rng.sample(source_overlap_ids, new_num_overlap)
    new_bboxes_ids = new_overlap_ids.copy()
    new_segmentations_ids = new_overlap_ids.copy()
    new_train_ids = new_overlap_ids.copy()

    # add the `new_num_train_segmentation_ids - new_num_overlap`, that are not in the overlap
    additional_segmentation_ids = rng.sample(
        [uid for uid in source_seg_ids if uid not in source_overlap_ids],
        new_num_train_segmentation_ids - new_num_overlap,
    )
    new_segmentations_ids += additional_segmentation_ids
    new_train_ids += additional_segmentation_ids

    # add the (`new_num_train_bbox_ids - num_num_overlap`) segmentations, that are not in the overlap
    additional_bbox_ids = rng.sample(
        [uid for uid in source_train_bbox_ids if uid not in source_overlap_ids],
        new_num_train_bbox_ids - new_num_overlap,
    )
    new_bboxes_ids += additional_bbox_ids
    new_train_ids += additional_bbox_ids

    # then, fill the rest of the new train.
    num_to_sample = num_train_samples - len(new_train_ids)
    available_pool = [uid for uid in source_train_df["StudyInstanceUID"] if uid not in new_train_ids]
    new_train_ids += rng.sample(
        available_pool,
        min(num_to_sample, len(available_pool)),  # Avoid sampling more than available
    )

    train = source_train_df[source_train_df["StudyInstanceUID"].isin(new_train_ids)].copy()
    train.to_csv(public_dir / "train.csv", index=False)

    train_bboxes = source_bbox_df[
        source_bbox_df["StudyInstanceUID"].isin(new_bboxes_ids)
    ].copy()
    train_bboxes.to_csv(public_dir / "train_bounding_boxes.csv", index=False)

    answers = source_train_df[~source_train_df["StudyInstanceUID"].isin(new_train_ids)].copy()
    # columns become rows for the test and sample submission, so also for answers
    answers = answers.melt(
        id_vars="StudyInstanceUID", var_name="prediction_type", value_name="fractured"
    )
    answers["row_id"] = answers["StudyInstanceUID"] + "_" + answers["prediction_type"]
    answers.to_csv(private_dir / "answers.csv", index=False)

    sample_submission = answers[["row_id", "fractured"]].copy()
    sample_submission["fractured"] = 0.5
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    public_test = answers.drop(columns=["fractured"]).copy()
    public_test.to_csv(public_dir / "test.csv", index=False)

    # assert that the melting worked
    if answers["StudyInstanceUID"].nunique() > 0:
        assert answers["StudyInstanceUID"].nunique() * 8 == len(
            answers
        ), "Melting failed, incorrect length"
    assert answers.columns.tolist() == [
        "StudyInstanceUID",
        "prediction_type",
        "fractured",
        "row_id",
    ], "Melting went wrong, columns are wrong"

    # column checks
    train_cols = ["StudyInstanceUID", "patient_overall", "C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    assert train.columns.tolist() == train_cols, "Train columns are wrong"
    bbox_cols = ["StudyInstanceUID", "x", "y", "width", "height", "slice_number"]
    assert train_bboxes.columns.tolist() == bbox_cols, "Bounding box columns are wrong"
    test_cols = ["StudyInstanceUID", "prediction_type", "row_id"]
    assert public_test.columns.tolist() == test_cols, "Test columns are wrong"
    submission_cols = ["row_id", "fractured"]
    assert sample_submission.columns.tolist() == submission_cols, "Submission columns are wrong"

    # check that test and train dont share study instance ids
    assert set(train["StudyInstanceUID"]).isdisjoint(
        set(public_test["StudyInstanceUID"].unique())
    ), "Train and test share study instance ids"

    # Now that splitting is done, copy over images accordingly
    (public_dir / "segmentations").mkdir(exist_ok=True)
    for file_id in tqdm(
        new_segmentations_ids,
        desc=f"Copying segmentations to {public_dir.name}",
        total=len(new_segmentations_ids),
    ):
        shutil.copyfile(
            src=raw_segmentations_path / f"{file_id}.nii",
            dst=public_dir / "segmentations" / f"{file_id}.nii",
        )

    (public_dir / "train_images").mkdir(exist_ok=True)
    for study_id in tqdm(
        train["StudyInstanceUID"],
        desc=f"Copying train images to {public_dir.name}",
        total=len(train),
        unit="StudyInstance",
    ):
        shutil.copytree(
            src=raw_images_path / study_id,
            dst=public_dir / "train_images" / study_id,
            dirs_exist_ok=True,
        )
    (public_dir / "test_images").mkdir(exist_ok=True)
    for study_id in tqdm(
        public_test["StudyInstanceUID"].unique(),
        desc=f"Copying test images to {public_dir.name}",
        total=public_test["StudyInstanceUID"].nunique(),
        unit="StudyInstance",
    ):
        shutil.copytree(
            src=raw_images_path / study_id,
            dst=public_dir / "test_images" / study_id,
            dirs_exist_ok=True,
        )

    return train, train_bboxes, new_segmentations_ids


def prepare(raw: Path, public: Path, private: Path):
    rng = random.Random(0)

    # there are two subsets of training data:

    # 1. one of instances that have bounding boxes
    # 2. one of instances that have segmentations

    # we need to preserve the ratios of the sizes of these subsets to the total train samples

    # additionally, there is an overlap between the two subsets
    # we need to preserve this overlap

    DEV = False
    old_train = read_csv(raw / "train.csv")

    num_old_train = len(old_train)
    if DEV:
        # This DEV logic is preserved from the original script to ensure
        # identical behavior if ever enabled. It is currently inactive.
        DEV_RATIO = 0.175
        num_old_train = round(DEV_RATIO * num_old_train)
        # The complex DEV logic from the original script is not fully ported
        # as it was intertwined with the main logic and is disabled by default.
        # This simplified version just subsamples the main dataframe.
        old_train = old_train.sample(n=num_old_train, random_state=0)

    # 2019 train folders (StudyInstanceUIDs), 1500 test folders, 2019 / (1500 + 2019) ~ 0.60 original train ratio
    # each folder has ~ 300 images
    # We use 0.1 ratio to avoid taking too many samples out of train
    TRAIN_RATIO = 0.1

    # Load all raw source data once
    old_train_bboxes = read_csv(raw / "train_bounding_boxes.csv")
    old_train_segmentation_path = raw / "segmentations"
    old_train_segmentation_ids = sorted([f.stem for f in old_train_segmentation_path.glob("*.nii")])

    # === Step 1: Perform the original data split to create `public` and `private` ===
    # This call produces the main train/test split. The outputs in `public` and
    # `private` will be identical to the original script's output.
    # We capture the resulting training set data to be used as the source for our next split.
    train_df, train_bboxes_df, train_seg_ids = _split_and_save(
        source_train_df=old_train,
        source_bbox_df=old_train_bboxes,
        source_seg_ids=old_train_segmentation_ids,
        raw_images_path=raw / "train_images",
        raw_segmentations_path=raw / "segmentations",
        train_ratio=TRAIN_RATIO,
        rng=rng,
        public_dir=public,
        private_dir=private,
    )

    # === Step 2: Perform a second split on the new training set to create a validation set ===
    # This call takes the *training set* from the first split (`train_df`) and
    # splits it again using the exact same logic and ratio.
    # The results are saved to the new `public_val` and `private_val` directories.
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    _split_and_save(
        source_train_df=train_df,
        source_bbox_df=train_bboxes_df,
        source_seg_ids=train_seg_ids,
        raw_images_path=raw / "train_images",  # Image source is still the main raw folder
        raw_segmentations_path=raw / "segmentations",
        train_ratio=TRAIN_RATIO,  # Use the same split ratio
        rng=rng,
        public_dir=public_val,
        private_dir=private_val,
    )