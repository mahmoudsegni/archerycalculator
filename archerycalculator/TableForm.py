from wtforms import Form, validators, SearchField


class HandicapTableForm(Form):
    round1 = SearchField("Round1", [validators.InputRequired("Please provide.")])
    round2 = SearchField("Round2")
    round3 = SearchField("Round3")
    round4 = SearchField("Round4")
    round5 = SearchField("Round5")
    round6 = SearchField("Round6")
    round7 = SearchField("Round7")


class ClassificationTableForm(Form):
    bowstyle = SearchField("Bowstyle", [validators.InputRequired("Please provide.")])
    gender = SearchField(
        "Gender under AGB", [validators.InputRequired("Please provide.")]
    )
    age = SearchField("Age category", [validators.InputRequired("Please provide.")])