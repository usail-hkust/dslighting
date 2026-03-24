from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # test.csv has features (Booking_ID + features), sample_result.csv has booking_status
    test_file = raw / 'test.csv'
    answer_file = raw / 'sample_result.csv'

    if test_file.exists():
        # Copy test.csv (features) to public/test.csv
        shutil.copy2(test_file, public / 'test.csv')
        test_df = pd.read_csv(test_file)
        num_rows = len(test_df)

        # Create answer_df from sample_result.csv (which has booking_status)
        if answer_file.exists():
            answer_col = pd.read_csv(answer_file)
            answer_df = pd.DataFrame({'Booking_ID': test_df['Booking_ID'], 'booking_status': answer_col['booking_status']})
        else:
            answer_df = pd.DataFrame({'Booking_ID': test_df['Booking_ID'], 'booking_status': ['Not_Canceled'] * num_rows})
        answer_df.to_csv(private / 'answer.csv', index=False)

    # Create sample_submission template
    if test_file.exists():
        test_df = pd.read_csv(test_file)
        sample_sub = pd.DataFrame({'Booking_ID': test_df['Booking_ID'], 'booking_status': ['Not_Canceled'] * len(test_df)})
        sample_sub.to_csv(public / 'sample_submission.csv', index=False)

    # Copy train data
    train_file = raw / 'Hotel Reservations.csv'
    if train_file.exists():
        shutil.copy2(train_file, public / 'train.csv')

    # Copy README
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
