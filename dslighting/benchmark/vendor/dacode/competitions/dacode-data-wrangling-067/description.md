## About Dataset

## Dataset Information
This data is from Open Source Mental Illness (OSMI) using survey data from years 2014, 2016, 2017, 2018 and 2019. Each survey measures and attitudes towards mental health and frequency of mental health disorders in the tech workplace.** ** The raw data was processed using Python, SQL and Excel for cleaning and manipulation. Steps involved in cleaning were * Similar questions were group together
* Values for answers were made consistent (ie 1 == 1.0)
* Fixing spelling errors ## Content The SQLite database contains 3 tables. Survey, Question, and Answer. Survey (PRIMARY KEY INT SurveyID, TEXT Description)
Question (PRIMARY KEY QuestionID, TEXT QuestionText)
Answer (PRIMARY/FOREIGN KEY SurveyID, PRIMARY KEY UserID, PRIMARY/FOREIGN KEY QuestionID, TEXT AnswerText) SuveyID are simply survey year ie 2014, 2016, 2017, 2018, 2019.
The same question can be used for multiple surveys
Answer table is a composite table with multiple primary keys. SurveyID and QuestionID are FOREIGN KEYS.
Some questions can contain multiple answers, thus the same user can appear more than once for that questionid. ### Common SQL queries #### query text information for Questionid SELECT * FROM Question where QuestionID = 13; #### query all answers for specified Questionid SELECT AnswerText FROM Answer where QuestionID = 13; #### query distribution of answer given questionid SELECT AnswerText, COUNT(AnswerText) from Answer where QuestionID = 13 group by AnswerText; #### query distribution of answer given questionid and survey year SELECT AnswerText, COUNT(AnswerText) from Answer where QuestionID = 1 and surveyid = 2016 group by AnswerText; #### query number of participants for each survey SELECT surveyid, COUNT(DISTINCT(userid)) FROM answer GROUP BY surveyid;
