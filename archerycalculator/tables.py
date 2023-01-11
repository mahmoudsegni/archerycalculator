from flask import (
    Blueprint,
    render_template,
    request,
)
import numpy as np

from archerycalculator.db import query_db, sql_to_dol

from archeryutils import rounds
from archeryutils.handicaps import handicap_equations as hc_eq
from archeryutils.classifications import classifications as class_func

from archerycalculator import TableForm, utils

bp = Blueprint("tables", __name__, url_prefix="/tables")


@bp.route("/handicap", methods=("GET", "POST"))
def handicap_tables():

    form = TableForm.HandicapTableForm(request.form)

    roundnames = sql_to_dol(query_db("SELECT code_name,round_name FROM rounds"))
    all_rounds = utils.indoor_display_filter(
        dict(zip(roundnames["code_name"], roundnames["round_name"]))
    )

    if request.method == "POST" and form.validate():
        error = None

        all_rounds_objs = rounds.read_json_to_round_dict(
            [
                "AGB_outdoor_imperial.json",
                "AGB_outdoor_metric.json",
                "AGB_indoor.json",
                "WA_outdoor.json",
                "WA_indoor.json",
                "WA_field.json",
                "IFAA_field.json",
                "Custom.json",
            ]
        )

        # Get form results
        rounds_req = []
        rounds_comp = []
        for i in range(7):
            if request.form[f"round{i+1}"]:
                rounds_req.append(request.form[f"round{i+1}"])
                if request.form.getlist(f"round{i+1}_compound"):
                    rounds_comp.append(True)
                else:
                    rounds_comp.append(False)

        allowance_table = False
        if request.form.getlist("allowance"):
            allowance_table = True

        round_objs = []
        for (round_i, comp_i) in zip(rounds_req, rounds_comp):
            round_codename = query_db(
                "SELECT code_name FROM rounds WHERE round_name IS (?)",
                [round_i],
                one=True,
            )["code_name"]
            if len(round_codename) == 0:
                error = f"Invalid round name '{round_i}'. Please select from dropdown."

            # Check if we need compound scoring
            if comp_i:
                round_codename = utils.get_compound_codename(round_codename)

            # Get the appropriate rounds from the database
            round_objs.append(all_rounds_objs[round_codename])

        # Generate the handicap params
        hc_params = hc_eq.HcParams()

        results = np.zeros([151, len(round_objs) + 1])
        results[:, 0] = np.arange(0, 151).astype(np.int32)
        for i, round_obj_i in enumerate(round_objs):
            results[:, i + 1] = hc_eq.score_for_round(
                round_obj_i, results[:, 0], "AGB", hc_params
            )[0].astype(np.int32)

        if allowance_table:
            results[:, 1:] = 1440 - results[:, 1:]
        else:
            # Clean gaps where there are multiple HC for one score
            # TODO: This assumes scores are running highest to lowest.
            #  AA and AA2 will only work if hcs passed in reverse order (large to small)
            # TODO: setting fill to -9999 is a bit hacky to get around jinja interpreting
            #  0, NaN, and None as the same thing. Consider finding better solution.
            for irow, row in enumerate(results[:-1, 1:]):
                for jscore, score in enumerate(row):
                    if results[irow, jscore + 1] == results[irow + 1, jscore + 1]:
                        results[irow, jscore + 1] = -9999

        if error is None:
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

    bowstylelist = sql_to_dol(query_db("SELECT bowstyle,disciplines FROM bowstyles"))[
        "bowstyle"
    ]
    genderlist = sql_to_dol(query_db("SELECT gender FROM genders"))["gender"]
    agelist = sql_to_dol(query_db("SELECT age_group FROM ages"))["age_group"]
    classlist = sql_to_dol(query_db("SELECT shortname FROM classes"))["shortname"]

    # Load form and set defaults
    form = TableForm.ClassificationTableForm(
        request.form, bowstyle=bowstylelist[1], gender=genderlist[1], age=agelist[1]
    )
    form.bowstyle.choices = bowstylelist
    form.gender.choices = genderlist
    form.age.choices = agelist

    if request.method == "POST" and form.validate():
        error = None

        # Get form results and store for return
        bowstyle = request.form["bowstyle"]
        gender = request.form["gender"]
        age = request.form["age"]
        discipline = request.form["discipline"]

        results = {}

        # Check the inputs are all valid
        bowstylecheck = query_db(
            "SELECT id FROM bowstyles WHERE bowstyle IS (?)", [bowstyle]
        )
        if len(bowstylecheck) == 0:
            error = "Invalid bowstyle. Please select from dropdown."
        results["bowstyle"] = bowstyle

        gendercheck = query_db("SELECT id FROM genders WHERE gender IS (?)", [gender])
        if len(gendercheck) == 0:
            error = "Please select gender from dropdown options."
        results["gender"] = gender

        agecheck = query_db("SELECT id FROM ages WHERE age_group IS (?)", [age])
        if len(agecheck) == 0:
            error = "Invalid age group. Please select from dropdown."
        results["age"] = age

        if discipline in ["outdoor"]:
            use_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE location IN ('outdoor') AND body in ('AGB','WA')"
                )
            )

            # Perform filtering based upon category to make more aesthetic and avoid duplicates
            roundsdicts = dict(zip(use_rounds["code_name"], use_rounds["round_name"]))
            filtered_names = utils.check_blacklist(
                use_rounds["code_name"], age, gender, bowstyle
            )
            round_names = [
                roundsdicts[key]
                for key in list(roundsdicts.keys())
                if key in filtered_names
            ]
            use_rounds = {"code_name": filtered_names, "round_name": round_names}

            results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
            for i, round_i in enumerate(use_rounds["code_name"]):
                results[i, :] = np.asarray(
                    class_func.AGB_outdoor_classification_scores(
                        round_i, bowstyle, gender, age
                    )
                )
        elif discipline in ["indoor"]:
            # TODO: This is a bodge - put indoor classes in database properly and fetch above!
            classlist = ["A", "B", "C", "D", "E", "F", "G", "H", "UC"]

            use_rounds = sql_to_dol(
                query_db(
                    "SELECT code_name,round_name FROM rounds WHERE location IN ('indoor') AND body in ('AGB','WA')"
                )
            )
            # Filter out compound rounds for non-recurve and vice versa
            # TODO: This is pretty horrible... is there a better way?
            roundsdicts = dict(zip(use_rounds["code_name"], use_rounds["round_name"]))
            noncompoundroundnames = utils.indoor_display_filter(roundsdicts)
            codenames = [
                key
                for key in list(roundsdicts.keys())
                if roundsdicts[key] in noncompoundroundnames
            ]
            if bowstyle.lower() in ["compound"]:
                codenames = utils.get_compound_codename(codenames)
            use_rounds = {"code_name": codenames, "round_name": noncompoundroundnames}

            results = np.zeros([len(use_rounds["code_name"]), len(classlist) - 1])
            for i, round_i in enumerate(use_rounds["code_name"]):
                results[i, :] = np.asarray(
                    class_func.AGB_indoor_classification_scores(
                        round_i, bowstyle, gender, age
                    )
                )
        else:
            # Should never get here... placeholder for field...
            # use_rounds = sql_to_dol(query_db("SELECT code_name FROM rounds WHERE location IN ('field') AND body in ('AGB','WA')"))
            # results = np.zeros([len(use_rounds["codename"]), len(classlist) - 1])
            # for i, round_i in enumerate(use_rounds["codename"]):
            #     results[i, :] = np.asarray(
            #         class_func.AGB_field_classification_scores(
            #             round_i, bowstyle, gender, age
            #         )

            pass

        # Add roundnames on to the end then flip for printing
        roundnames = [round_i for round_i in use_rounds["round_name"]]
        results = np.flip(
            np.concatenate(
                (results.astype(int), np.asarray(roundnames)[:, None]), axis=1
            ),
            axis=1,
        )
        classes = classlist[-2::-1]

        if error is None:
            # Return the results
            # Flip array so lowest class on left for printing
            return render_template(
                "classification_tables.html",
                form=form,
                results=results.astype(str),
                classes=classes,
            )
        else:
            # If errors reload default with error message
            return render_template(
                "classification_tables.html",
                form=form,
                error=error,
            )

    # If first visit load the default form with no inputs
    return render_template(
        "classification_tables.html",
        form=form,
        error=None,
    )
