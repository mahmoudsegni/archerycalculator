from flask import (
    Blueprint,
    render_template,
    request,
)
import numpy as np

from archerycalculator.db import get_db, query_db

from archeryutils import rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.handicaps import handicap_functions as hc_func
from archeryutils.classifications import classifications as class_func

from archerycalculator import TableForm

bp = Blueprint("tables", __name__, url_prefix="/tables")


@bp.route("/handicap", methods=("GET", "POST"))
def handicap_tables():

    database = get_db()

    form = TableForm.HandicapTableForm(request.form)

    all_rounds = query_db("SELECT round_name FROM rounds")

    if request.method == "POST" and form.validate():
        error = None

        all_rounds_objs = rounds.read_json_to_round_dict(
            [
                "AGB_outdoor_imperial.json",
                "AGB_outdoor_metric.json",
                "AGB_indoor.json",
                "WA_outdoor.json",
                "WA_indoor.json",
                "Custom.json",
            ]
        )

        # Get essential form results
        rounds_req = []
        rounds_req.append(request.form["round1"])
        rounds_req.append(request.form["round2"])
        rounds_req.append(request.form["round3"])
        rounds_req.append(request.form["round4"])
        rounds_req.append(request.form["round5"])
        rounds_req.append(request.form["round6"])
        rounds_req.append(request.form["round7"])

        rounds_req = [i for i in rounds_req if i]
        round_objs = []
        for round_i in rounds_req:
            roundcheck = query_db(
                "SELECT id FROM rounds WHERE round_name IS (?)", [round_i]
            )
            if len(roundcheck) == 0:
                error = f"Invalid round name '{round_i}'. Please select from dropdown."

            # Get the appropriate rounds from the database
            round_objs.append(
                all_rounds_objs[
                    query_db(
                        "SELECT code_name FROM rounds WHERE round_name IS (?)",
                        [round_i], one=True
                    )["code_name"]
                ]
            )

        # Generate the handicap params
        hc_params = hc_eq.HcParams()

        results = np.zeros([151, len(round_objs) + 1])
        results[:, 0] = np.arange(0, 151).astype(np.int32)
        for i, round_obj_i in enumerate(round_objs):
            results[:, i + 1] = hc_eq.score_for_round(
                round_obj_i, results[:, 0], "AGB", hc_params
            )[0].astype(np.int32)

        # Clean gaps where there are multiple HC for one score
        # TODO: This assumes scores are running highest to lowest.
        #  AA and AA2 will only work if hcs passed in reverse order (large to small)
        # TODO: setting fill to -9999 is a bit hacky to get around jinja interpreting
        #  0, NaN, and None as the same thing. Consider finding better solution.
        for irow, row in enumerate(results[:-1, 1:]):
            for jscore, score in enumerate(row):
                if results[irow, jscore+1] == results[irow+1, jscore+1]:
                    results[irow, jscore+1] = -9999

        if error is None:
            # Calculate the handicap
            # Generate table for selected rounds
            # Need to add non-outdoor rounds to database

            # Return the results
            return render_template(
                "handicap_tables.html",
                rounds=all_rounds,
                form=form,
                roundnames=rounds_req,
                results=results,
            )
        else:
            # If errors reload default with error message
            return render_template(
                "handicap_tables.html",
                rounds=all_rounds,
                form=form,
                error=error,
            )

    # If first visit load the default form with no inputs
    return render_template(
        "handicap_tables.html",
        form=form,
        rounds=all_rounds,
        error=None,
    )


@bp.route("/classification", methods=("GET", "POST"))
def classification_tables():

    database = get_db()

    all_bowstyles = database.execute(
        "SELECT bowstyle,disciplines FROM bowstyles"
    ).fetchall()
    all_genders = query_db("SELECT gender FROM genders")
    all_ages = query_db("SELECT age_group FROM ages")
    all_rounds = query_db("SELECT round_name FROM rounds")
    all_classes = query_db("SELECT shortname FROM classes")

    form = TableForm.ClassificationTableForm(request.form)

    if request.method == "POST" and form.validate():
        error = None

        # Get form results and store for return
        bowstyle = request.form["bowstyle"]
        gender = request.form["gender"]
        age = request.form["age"]
       
        results = {}

        # Check the inputs are all valid
        bowstylecheck = query_db(
            "SELECT id FROM bowstyles WHERE bowstyle IS (?)", [bowstyle]
        )
        if len(bowstylecheck) == 0:
            error = "Invalid bowstyle. Please select from dropdown."
        results["bowstyle"] = bowstyle

        gendercheck = query_db(
            "SELECT id FROM genders WHERE gender IS (?)", [gender]
        )
        if len(gendercheck) == 0:
            error = "Please select gender from dropdown options."
        results["gender"] = gender

        agecheck = query_db(
            "SELECT id FROM ages WHERE age_group IS (?)", [age]
        )
        if len(agecheck) == 0:
            error = "Invalid age group. Please select from dropdown."
        results["age"] = age

        all_rounds = rounds.read_json_to_round_dict(
            [
                "AGB_outdoor_imperial.json",
                "AGB_outdoor_metric.json",
                # "AGB_indoor.json",
                "WA_outdoor.json",
                # "WA_indoor.json",
                # "Custom.json",
            ]
        )

        results = np.zeros([len(all_rounds), len(all_classes)-1])
        # Loop through and get scores
        for i, round_i in enumerate(all_rounds):
            results[i, :] = np.asarray(class_func.AGB_outdoor_classification_scores(round_i, bowstyle, gender, age))
            # Worry about deleting rows next...
        
        # Add roundnames on to the end then flip for printing
        roundnames = [round_i["round_name"] for round_i in query_db("SELECT round_name FROM rounds")]
        results = np.flip(np.concatenate((results.astype(int), np.asarray(roundnames)[:, None]), axis=1), axis=1)
        classes = all_classes[-2::-1]

        if error is None:
            # Return the results
            # Flip array so lowest class on left for printing
            return render_template(
                "classification_tables.html",
                bowstyles=all_bowstyles,
                genders=all_genders,
                ages=all_ages,
                form=form,
                results=results.astype(str),
                classes=classes
            )
        else:
            # If errors reload default with error message
            return render_template(
                "classification_tables.html",
                bowstyles=all_bowstyles,
                genders=all_genders,
                ages=all_ages,
                form=form,
                error=error,
            )

    # If first visit load the default form with no inputs
    return render_template(
        "classification_tables.html",
        form=form,
        bowstyles=all_bowstyles,
        genders=all_genders,
        ages=all_ages,
        error=None,
    )