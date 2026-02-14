import shutil
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def _process_and_save_split(
    train_game_play_ids: list,
    test_game_play_ids: list,
    raw_path: Path,
    public_path: Path,
    private_path: Path,
    old_train_labels_df: pd.DataFrame,
    old_train_baseline_helmets_df: pd.DataFrame,
    old_train_player_tracking_df: pd.DataFrame,
    old_train_video_metadata_df: pd.DataFrame,
):
    """
    A helper function to process and save a single data split (e.g., train/test or train_val/test_val).

    This function filters raw dataframes based on game play IDs, saves the resulting CSVs,
    copies the corresponding video files, and creates a sample submission file.
    The output filenames are fixed to ensure consistent structure across different splits.
    """
    public_path.mkdir(exist_ok=True, parents=True)
    private_path.mkdir(exist_ok=True, parents=True)
    (public_path / "train").mkdir(exist_ok=True)
    (public_path / "test").mkdir(exist_ok=True)

    # Filter and save train/test labels
    new_train = old_train_labels_df[
        old_train_labels_df["game_play"].isin(train_game_play_ids)
    ]
    new_test = old_train_labels_df[
        old_train_labels_df["game_play"].isin(test_game_play_ids)
    ]
    assert set(new_train["contact_id"]).isdisjoint(
        set(new_test["contact_id"])
    ), "Train and test label share samples!"

    new_train.to_csv(public_path / "train_labels.csv", index=False)
    new_test.to_csv(private_path / "test.csv", index=False)

    # Filter and save baseline helmets
    new_train_baseline_helmets = old_train_baseline_helmets_df[
        old_train_baseline_helmets_df["game_play"].isin(train_game_play_ids)
    ]
    new_test_baseline_helmets = old_train_baseline_helmets_df[
        old_train_baseline_helmets_df["game_play"].isin(test_game_play_ids)
    ]

    new_train_baseline_helmets.to_csv(
        public_path / "train_baseline_helmets.csv", index=False
    )
    new_test_baseline_helmets.to_csv(
        public_path / "test_baseline_helmets.csv", index=False
    )

    # Filter and save player tracking
    new_train_player_trackings = old_train_player_tracking_df[
        old_train_player_tracking_df["game_play"].isin(train_game_play_ids)
    ]
    new_test_player_trackings = old_train_player_tracking_df[
        old_train_player_tracking_df["game_play"].isin(test_game_play_ids)
    ]

    new_train_player_trackings.to_csv(
        public_path / "train_player_tracking.csv", index=False
    )
    new_test_player_trackings.to_csv(
        public_path / "test_player_tracking.csv", index=False
    )

    # Filter and save video metadata
    new_train_video_metadata = old_train_video_metadata_df[
        old_train_video_metadata_df["game_play"].isin(train_game_play_ids)
    ]
    new_test_video_metadata = old_train_video_metadata_df[
        old_train_video_metadata_df["game_play"].isin(test_game_play_ids)
    ]

    new_train_video_metadata.to_csv(
        public_path / "train_video_metadata.csv", index=False
    )
    new_test_video_metadata.to_csv(
        public_path / "test_video_metadata.csv", index=False
    )

    # Copy over videos
    print(f"Copying videos to {public_path.name}...")
    for game_play_type in ["All29", "Endzone", "Sideline"]:
        for game_play in tqdm(
            new_train["game_play"].unique(),
            desc=f"Copying train videos ({game_play_type})",
        ):
            shutil.copyfile(
                src=raw_path / "train" / f"{game_play}_{game_play_type}.mp4",
                dst=public_path / "train" / f"{game_play}_{game_play_type}.mp4",
            )

        for game_play in tqdm(
            new_test["game_play"].unique(),
            desc=f"Copying test videos ({game_play_type})",
        ):
            shutil.copyfile(
                src=raw_path / "train" / f"{game_play}_{game_play_type}.mp4",
                dst=public_path / "test" / f"{game_play}_{game_play_type}.mp4",
            )

    # Check integrity of the files copied
    num_train_videos_found = len(list(public_path.glob("train/*.mp4")))
    num_test_videos_found = len(list(public_path.glob("test/*.mp4")))
    num_expected_train_videos = len(new_train["game_play"].unique()) * 3
    num_expected_test_videos = len(new_test["game_play"].unique()) * 3

    assert (
        num_train_videos_found == num_expected_train_videos
    ), f"Expected {num_expected_train_videos} images, found {num_train_videos_found}"
    assert (
        num_test_videos_found == num_expected_test_videos
    ), f"Expected {num_expected_test_videos} images, found {num_test_videos_found}"

    # Create a sample submission file
    submission_df = pd.DataFrame(
        {
            "contact_id": new_test["contact_id"],
            "contact": 0,
        }
    )
    submission_df.to_csv(public_path / "sample_submission.csv", index=False)


def prepare(raw: Path, public: Path, private: Path):
    # Load all raw dataframes once to improve efficiency
    old_train_labels = pd.read_csv(raw / "train_labels.csv")
    old_train_baseline_helmets = pd.read_csv(raw / "train_baseline_helmets.csv")
    old_train_player_tracking = pd.read_csv(raw / "train_player_tracking.csv")
    old_train_video_metadata = pd.read_csv(raw / "train_video_metadata.csv")

    # --- Original Data Split (Train/Test) ---
    # Create train, test from train split. Ensure train, test come from different game plays
    unique_game_play = old_train_labels["game_play"].unique()
    new_train_game_play, new_test_game_play = train_test_split(
        unique_game_play, test_size=0.1, random_state=0
    )

    print("--- Processing original train/test split ---")
    _process_and_save_split(
        train_game_play_ids=new_train_game_play,
        test_game_play_ids=new_test_game_play,
        raw_path=raw,
        public_path=public,
        private_path=private,
        old_train_labels_df=old_train_labels,
        old_train_baseline_helmets_df=old_train_baseline_helmets,
        old_train_player_tracking_df=old_train_player_tracking,
        old_train_video_metadata_df=old_train_video_metadata,
    )
    print("--- Original split processing complete. ---\n")

    # --- New Validation Data Split (Train_val/Test_val) ---
    # Define new paths for the validation split
    public_val = public.parent / "public_val"
    private_val = private.parent / "private_val"

    # Split the *training set* again to create a validation set.
    # Use the same logic and random_state for consistency.
    train_val_game_play, test_val_game_play = train_test_split(
        new_train_game_play, test_size=0.1, random_state=0
    )

    print("--- Processing validation train/test split ---")
    _process_and_save_split(
        train_game_play_ids=train_val_game_play,
        test_game_play_ids=test_val_game_play,
        raw_path=raw,
        public_path=public_val,
        private_path=private_val,
        old_train_labels_df=old_train_labels,
        old_train_baseline_helmets_df=old_train_baseline_helmets,
        old_train_player_tracking_df=old_train_player_tracking,
        old_train_video_metadata_df=old_train_video_metadata,
    )
    print("--- Validation split processing complete. ---")