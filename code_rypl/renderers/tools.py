sport_abrev_to_formal_name = {
    "hky": "Hockey",
    "bball": "Basketball",
    "soc": "Soccer",
    "baseb": "Baseball",
    "softb": "Softball",
    "lax": "Lacrosse",
    "fb": "Football",
    "fhky": "Field Hockey",
}

category_formal_to_variations = {
    "Men's": {"m", "men", "man", "male", "masc"},
    "Women's": {"w", "women", "woman", "female", "femme"},
    "None": {"n", "none", "enby"},
}

_prepositions = {
    "the",
    "at",
    "in",
    "from",
    "over",
    "of",
    "and",
    "upon",
    "with",
    "on",
    "to",
    "by",
}

# TODO: add methods to check if sport, category, and season are valid so they can be
#   highlighted in the UI when the user types bad formats. but remember to be
#   conservative and only give false when known to be bad. (eg "2" for year)


def normalize_school(school: str) -> str:
    if school.startswith(":"):
        return ":" + school.lstrip(":").strip()
    else:
        return " ".join(
            map(
                lambda s: (  # TODO: make this not crap
                    (s.capitalize() if s.lower() == s else s)
                    if s.lower() not in _prepositions
                    else s.lower()
                ),
                filter(None, school.split()),
            )
        )


def normalize_sports(sport: str) -> str:

    # if the starts starts with a colon then only stip (including the space after the colon)
    if sport.startswith(":"):
        return ":" + sport.lstrip(":").strip()

    matchable = sport.replace(" ", "").strip().lower()

    # if the sport a value in the known_sport_abbrevs then return the key
    for abbrev, full_name in sport_abrev_to_formal_name.items():
        if matchable == abbrev:
            return full_name
        elif matchable == full_name.lower().replace(" ", ""):
            return full_name
    else:
        return sport.strip()


def normalize_category(raw_cato: str) -> str:
    # if the starts starts with a colon then only stip (including the space after the colon)
    if raw_cato.startswith(":"):
        return ":" + raw_cato.lstrip(":").strip()

    matchable = raw_cato.replace(" ", "").strip().lower().lstrip("'s")

    for formal, variations in category_formal_to_variations.items():
        if matchable in variations:
            return formal
    else:
        return raw_cato.strip()


def normalize_season(season: str) -> str:
    if season.startswith(":"):
        return ":" + season.lstrip(":").strip()

    end_raw: str | None
    if "-" in season:
        start_raw, end_raw = filter(None, season.split("-"))
    else:
        start_raw, end_raw = season, None

    start = start_raw.strip()

    if end_raw is None and len(start) == 4 and start.isnumeric():
        return f"{start}-{(int(start)+1)%100:02}"
    else:
        return season.strip()
