import pandas as pd
import re


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Grade the DABench submission.

    Args:
        submission: DataFrame with columns ['id', 'answer']
        answers: DataFrame with columns ['id', 'answer']

    Returns:
        float: 1.0 if exact match, 0.0 otherwise
    """
    try:
        # Both should have exactly one row
        if len(submission) != 1 or len(answers) != 1:
            return 0.0

        # Get the submission and answer strings
        submission_str = str(submission.iloc[0]['answer']).strip()
        answer_str = str(answers.iloc[0]['answer']).strip()

        # Parse all key-value pairs
        # Expected keys: ['country_with_highest_score']
        pattern = r'@(\w+)\[([^\]]+)\]'

        submission_dict = dict(re.findall(pattern, submission_str))
        answer_dict = dict(re.findall(pattern, answer_str))

        if not submission_dict or not answer_dict:
            print(f"Failed to parse: submission='{submission_str}', answer='{answer_str}'")
            return 0.0

        # Check if all keys match
        if set(submission_dict.keys()) != set(answer_dict.keys()):
            print(f"Key mismatch: submission has {set(submission_dict.keys())}, answer has {set(answer_dict.keys())}")
            return 0.0

        # Compare values
        all_match = True
        for key in answer_dict:
            submission_value = submission_dict[key]
            answer_value = answer_dict[key]

            # Try to compare as numbers
            try:
                sub_float = float(submission_value)
                ans_float = float(answer_value)
                if abs(sub_float - ans_float) >= 0.01:
                    print(f"Value mismatch for {key}: submission={sub_float}, answer={ans_float}")
                    all_match = False
                    break
            except ValueError:
                # Compare as strings (case-insensitive)
                if submission_value.lower() != answer_value.lower():
                    print(f"Value mismatch for {key}: submission='{submission_value}', answer='{answer_value}'")
                    all_match = False
                    break

        return 1.0 if all_match else 0.0

    except Exception as e:
        print(f"Error in grading: {e}")
        return 0.0
