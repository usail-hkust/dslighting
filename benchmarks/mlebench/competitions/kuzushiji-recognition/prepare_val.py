import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from sklearn.model_selection import train_test_split
from tqdm import tqdm

from mlebench.utils import extract, get_logger, read_csv

if TYPE_CHECKING:
    import pandas as pd

logger = get_logger(__name__)


def _create_split_files(
    train_df: "pd.DataFrame",
    test_df: "pd.DataFrame",
    public_dir: Path,
    private_dir: Path,
    raw_dir: Path,
):
    """
    Helper function to create all necessary files for a given train/test split.

    This function populates the public and private directories with the respective
    data (images, CSVs, submissions) based on the provided dataframes.
    """
    # Save the new train and test metadata
    train_df.to_csv(public_dir / "train.csv", index=False)
    test_df.to_csv(private_dir / "test.csv", index=False)

    # Copy images
    (public_dir / "train").mkdir(exist_ok=True)
    (public_dir / "test").mkdir(exist_ok=True)
    raw_img_dir = raw_dir / "train"

    for file_id in tqdm(train_df["image_id"], desc=f"Copying train images to {public_dir.name}"):
        shutil.copyfile(
            src=raw_img_dir / f"{file_id}.jpg",
            dst=public_dir / "train" / f"{file_id}.jpg",
        )

    for file_id in tqdm(test_df["image_id"], desc=f"Copying test images to {public_dir.name}"):
        shutil.copyfile(
            src=raw_img_dir / f"{file_id}.jpg",
            dst=public_dir / "test" / f"{file_id}.jpg",
        )

    assert len(list(public_dir.glob("train/*.jpg"))) == len(train_df)
    assert len(list(public_dir.glob("test/*.jpg"))) == len(test_df)

    # Create zips of the images
    logger.info(f"Re-zipping up new image directories for {public_dir.name}...")
    shutil.make_archive(str(public_dir / "train_images"), "zip", public_dir / "train")
    shutil.make_archive(str(public_dir / "test_images"), "zip", public_dir / "test")
    # Remove the directories for consistency with the kaggle data
    shutil.rmtree(public_dir / "train")
    shutil.rmtree(public_dir / "test")

    # Copy unicode_translation
    shutil.copyfile(
        src=raw_dir / "unicode_translation.csv",
        dst=public_dir / "unicode_translation.csv",
    )

    assert (public_dir / "train_images.zip").is_file()
    assert (public_dir / "test_images.zip").is_file()
    assert (public_dir / "unicode_translation.csv").is_file()

    # Make sample submission for new test set
    sample_submission = test_df.copy()
    # Same guess for all, as in original sample submission
    sample_submission["labels"] = "U+003F 1 1 U+FF2F 2 2"
    sample_submission.to_csv(public_dir / "sample_submission.csv", index=False)

    # Make a gold submission in private/ (useful for testing)
    # This submission takes the "class x y w h" labels from test and converts them to
    # "class x+1 y+1" labels (the +1 moves the coord into the  bbox, so that the metric picks it up)
    submission_labels = []
    for label in test_df["labels"]:
        # Labels have the form "class x y w h class x y w h class x y w h ... "
        label = label.split()
        new_label = []
        assert len(label) % 5 == 0
        classes, xs, ys = label[0::5], label[1::5], label[2::5]
        # +1 to xs and ys
        xs = [str(int(x) + 1) for x in xs]
        ys = [str(int(y) + 1) for y in ys]
        new_label = [f"{c} {x} {y}" for c, x, y in zip(classes, xs, ys)]
        submission_labels.append(" ".join(new_label))
    gold_submission = test_df.copy()
    gold_submission["labels"] = submission_labels
    gold_submission.to_csv(private_dir / "gold_submission.csv", index=False)

    assert len(gold_submission) == len(test_df)
    assert len(gold_submission) == len(sample_submission)


def prepare(raw: Path, public: Path, private: Path):
    """
    Splits the data in raw into public and private datasets with appropriate test/train splits.
    Additionally, creates a second train/validation split for local model development.
    """
    # Extract images so we can split the train images
    extract(raw / "train_images.zip", raw / "train")

    # Create train, test from train split
    old_train = read_csv(raw / "train.csv")

    # --- Original Split (for final evaluation) ---
    logger.info("Creating original train/test split for 'public' and 'private' directories...")
    new_train, new_test = train_test_split(old_train, test_size=0.1, random_state=0)

    _create_split_files(
        train_df=new_train,
        test_df=new_test,
        public_dir=public,
        private_dir=private,
        raw_dir=raw,
    )
    assert len(new_train) + len(new_test) == len(old_train)
    logger.info("Successfully created original split.")

    # --- New Validation Split (for local development) ---
    logger.info("Creating new train/validation split for 'public_val' and 'private_val' directories...")
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"
    public_val.mkdir(exist_ok=True)
    private_val.mkdir(exist_ok=True)

    # Split the original training data to create a new, smaller training set and a validation set.
    # The validation set size must be approx the same as the original test set size.
    # Original test size = 0.1 * total_data
    # Original train size = 0.9 * total_data
    # To make the new validation set size equal to the original test set size, we must take
    # a fraction of the `new_train` data: test_size * (0.9 * total) = 0.1 * total.
    # This means the required test_size = 0.1 / 0.9 = 1/9.
    train_val, test_val = train_test_split(new_train, test_size=1 / 9, random_state=0)

    _create_split_files(
        train_df=train_val,
        test_df=test_val,
        public_dir=public_val,
        private_dir=private_val,
        raw_dir=raw,
    )
    assert len(train_val) + len(test_val) == len(new_train)
    logger.info("Successfully created validation split.")