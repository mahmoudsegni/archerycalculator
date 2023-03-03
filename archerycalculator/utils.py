import numpy as np


def check_blacklist(roundlist, age, gender, bowstyle):
    """
    Filter indoor rounds to remove any with compound scoring for the purposes of
    display

    Parameters
    ----------
    roundlist : list
        list of archeryutils round codenames

    Returns
    -------
    list
        filtered version of the input list

    References
    ----------
    """

    blacklist = []

    blacklist.append("wa1440_90_small")
    blacklist.append("wa1440_70_small")
    blacklist.append("wa1440_60_small")

    # Gender
    if gender.lower() in ["male"]:
        blacklist.append("hereford")
        blacklist.append("long_metric_ladies")
        blacklist.append("wa1440_60")
        if age.lower().replace(" ", "") in ["50+"]:
            blacklist.append("metric_i")
        else:
            blacklist.append("wa1440_70")

    if gender.lower() in ["female"]:
        blacklist.append("bristol_i")
        blacklist.append("long_metric_i")
        if age.lower().replace(" ", "") in ["50+"]:
            blacklist.append("metric_ii")
        else:
            blacklist.append("wa1440_60")

    # Age
    if age.lower().replace(" ", "") in ["adult", "50+"]:
        blacklist.append("short_metric_i")
    else:
        blacklist.append("short_metric")

    # Bowstyle
    if bowstyle.lower() in ["compound"]:
        blacklist.append("metric_80_50")
    else:
        blacklist.append("wa720_50_c")

    if bowstyle.lower() in ["barebow"]:
        blacklist.append("metric_122_50")
    else:
        blacklist.append("wa720_50_b")

    saferounds = []
    for roundname in roundlist:
        if roundname not in blacklist:
            saferounds.append(roundname)

    return saferounds


def indoor_display_filter(rounddict):
    """
    Filter indoor rounds to remove any with compound scoring for the purposes of
    display

    Parameters
    ----------
    rounddict : dict
        dict of round data where the archeryutils codename is the key

    Returns
    -------
    list
        list of full round names from filtered version of the input dict

    References
    ----------
    """
    for roundname in list(rounddict.keys()):
        if "compound" in roundname:
            del rounddict[roundname]
    return [rounddict[round_i] for round_i in rounddict]


def get_compound_codename(round_codenames):
    """
    convert any indoor rounds with special compound scoring to the compound format

    Parameters
    ----------
    round_codenames : str or list of str
        list of str round codenames to check

    Returns
    -------
    round_codenames : str or list of str
        list of amended round codenames for compound

    References
    ----------
    """
    notlistflag = False
    if not isinstance(round_codenames, list):
        round_codenames = [round_codenames]
        notlistflag = True

    convert_dict = {
        "bray_i": "bray_i_compound",
        "bray_i_triple": "bray_i_compound_triple",
        "bray_ii": "bray_ii_compound",
        "bray_ii_triple": "bray_ii_compound_triple",
        "stafford": "stafford_compound",
        "portsmouth": "portsmouth_compound",
        "portsmouth_triple": "portsmouth_compound_triple",
        "vegas": "vegas_compound",
        "wa18": "wa18_compound",
        "wa18_triple": "wa18_compound_triple",
        "wa25": "wa25_compound",
        "wa25_triple": "wa25_compound_triple",
    }

    for i, codename in enumerate(round_codenames):
        if codename in convert_dict:
            round_codenames[i] = convert_dict[codename]
    if notlistflag:
        return round_codenames[0]
    else:
        return round_codenames


def check_alias(round_codename, age, gender, bowstyle):
    """
    select the 'appropriate' round from aliases

    Parameters
    ----------
    round_codename : str
        str round codename to check

    Returns
    -------
    round_codename : str
        amended round codenames

    References
    ----------
    """
    # York, Hereford, Bristols
    if (round_codename == "hereford") and (gender.lower() == "male"):
        round_codename = "bristol_i"
    if (round_codename == "bristol_i") and (gender.lower() == "female"):
        round_codename = "hereford"

    # WA1440s
    if round_codename == "metric_i":
        round_codename = "wa1440_70"
    if round_codename == "metric_ii":
        round_codename = "wa1440_60"

    # WA720s
    if (round_codename == "wa720_50_c") and (bowstyle.lower() != "compound"):
        round_codename = "metric_80_50"
    if (round_codename == "metric_80_50") and (bowstyle.lower() == "compound"):
        round_codename = "wa720_50_c"

    if (round_codename == "wa720_50_b") and (bowstyle.lower() != "barebow"):
        round_codename = "metric_122_50"
    if (round_codename == "metric_122_50") and (bowstyle.lower() == "barebow"):
        round_codename = "wa720_50_b"

    return round_codename


def order_rounds(rounds, age=None, gender=None, bowstyle=None):
    """
    Given an iterator of rounds, sort them into an approved order.

    Parameters
    ----------
    rounds : dict of str:str
        dictionary of round codenames mapped to their family

    Returns
    -------
    sorted_rounds : dict of str:str
        dict of sorted rounds input dict

    References
    ----------
    """

    # TODO Easy way to do this with dict? Otherwise should we bother?
    # Just in case, check for aliases and filter
    # if not any(arg is None for arg in (age, gender, bowstyle)):
    #     rounds = [check_alias(round, age, gender, bowstyle) for round in rounds]

    # Sort by family - rounds should already sorted within families. and filtered.
    order = [
            "york_hereford_bristol",
            "stgeorge_albion_windsor",
            "national",
            "western",
            "warwick",
            "american",
            "stnicholas",
            "wa1440",
            "metric1440",
            "wa900",
            "720",
            "metriclong",
            "metricshort",
            ]
    
    sorted_rounds = {}
    for family in order:
        if family == "720":
            # Special treatment needed to sort the wa720 and metric720 families
            sorted_rounds.update({key:value for (key,value) in rounds.items() if value == "wa720" and "wa720_50_c" not in key})
            sorted_rounds.update({key:value for (key,value) in rounds.items() if value == "metric720" and "metric_80" not in key})
            sorted_rounds.update({key:value for (key,value) in rounds.items() if value == "wa720" and "wa720_50_c" in key})
            sorted_rounds.update({key:value for (key,value) in rounds.items() if value == "metric720" and "metric_80" in key})
        else:
            sorted_rounds.update({ key:value for (key,value) in rounds.items() if value == family})

    return sorted_rounds


def rootfinding(x_min, x_max, f_root, *args):
    """
    For bracket and function find the value such that f=0

    Parameters
    ----------
    x_min, xmax : float
        bounds of the search bracket
    f_root : function
        function to minimise
    args :
        arguments to f_root

    Returns
    -------
    hc : float
        root of function

    References
    ----------
    """

    x = [x_min, x_max]
    f = [
        f_root(x[0], *args),
        f_root(x[1], *args),
    ]
    xtol = 1.0e-16
    rtol = 0.00
    xblk = 0.0
    fblk = 0.0
    scur = 0.0
    spre = 0.0
    dpre = 0.0
    dblk = 0.0
    stry = 0.0

    if abs(f[1]) <= f[0]:
        xcur = x[1]
        xpre = x[0]
        fcur = f[1]
        fpre = f[0]
    else:
        xpre = x[1]
        xcur = x[0]
        fpre = f[1]
        fcur = f[0]

    for i in range(50):
        if (fpre != 0.0) and (fcur != 0.0) and (np.sign(fpre) != np.sign(fcur)):
            xblk = xpre
            fblk = fpre
            spre = xcur - xpre
            scur = xcur - xpre
        if abs(fblk) < abs(fcur):
            xpre = xcur
            xcur = xblk
            xblk = xpre

            fpre = fcur
            fcur = fblk
            fblk = fpre

        delta = (xtol + rtol * abs(xcur)) / 2.0
        sbis = (xblk - xcur) / 2.0

        if (fcur == 0.0) or (abs(sbis) < delta):
            hc = xcur
            break

        if (abs(spre) > delta) and (abs(fcur) < abs(fpre)):
            if xpre == xblk:
                stry = -fcur * (xcur - xpre) / (fcur - xpre)
            else:
                dpre = (fpre - fcur) / (xpre - xcur)
                dblk = (fblk - fcur) / (xblk - xcur)
                stry = -fcur * (fblk - fpre) / (fblk * dpre - fpre * dblk)

            if 2 * abs(stry) < min(abs(spre), 3 * abs(sbis) - delta):
                # accept step
                spre = scur
                scur = stry
            else:
                # bisect
                spre = sbis
                scur = sbis
        else:
            # bisect
            spre = sbis
            scur = sbis
        xpre = xcur
        fpre = fcur
        if abs(scur) > delta:
            xcur += scur
        else:
            if sbis > 0:
                xcur += delta
            else:
                xcur -= delta

        fcur = f_root(xcur, *args)
        hc = xcur
    return hc


def group_icons(groupsize):
    if groupsize < 1.0e-2:
        return "fa-solid fa-spider"
    elif groupsize < 2.5e-2:
        return "fa-solid fa-eye"
    elif groupsize < 3.5e-2:
        return "fa-solid fa-egg"
    elif groupsize < 5.0e-2:
        return "fa-regular fa-lightbulb"
    elif groupsize < 8.0e-2:
        return "fa-solid fa-apple-whole"
    elif groupsize < 23.0e-2:
        return "fa-solid fa-volleyball"
    elif groupsize < 27.5e-2:
        return "fa-solid fa-basketball"
    elif groupsize < 35.0e-2:
        return "fa-solid fa-record-vinyl"
    elif groupsize < 45.0e-2:
        return "fa-solid fa-hat-wizard"
    elif groupsize < 55.0e-2:
        return "fa-solid fa-guitar"
    elif groupsize < 75.0e-2:
        return "fa-brands fa-linux"
    elif groupsize < 122.0e-2:
        return "fa-solid fa-bullseye"
    elif groupsize < 180.0e-2:
        return "fa-solid fa-car"
    else:
        return "fa-solid fa-earth-americas"
