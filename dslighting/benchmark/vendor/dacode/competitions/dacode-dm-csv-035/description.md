# dacode-dm-csv-035

## Instruction
Convert all time columns to Coordinated Universal Time (UTC) and record each user's pulled files based on their pid. If a user pulled multiple files within one pid, record these files separately.

## About Dataset
The dataset contains GitHub pull request history of the Scala language. It includes two main CSV files:
- `pulls.csv`: Contains pull request information including PR ID, user, date, and title
- `pull_files.csv`: Contains the files associated with each pull request The pull request times are in UTC, but commit times are in the local time of the author with timezone information.
