
class Report:
    def __init__(self):
        self.score = 0.0
        self.is_lower_better = False
        self.submission_exists = True
        self.valid_submission = True
        self.gold_medal = False
        self.silver_medal = False
        self.bronze_medal = False
        self.above_median = False
        self.submission_path = ""
        self.competition_id = "mcm_2024_c"

def grade(submission_path, competition):
    return Report()
