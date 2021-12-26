from __future__ import annotations
from typing import *

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

prepositions = {
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


def remove_prepositions(string: str) -> str:
    """
    Removes prepositions from a string.
    """
    if isescaped(string):
        return ":" + strip_escape(string)
    return " ".join(filter(lambda x: x not in prepositions, string.split()))


def abbreviate(string: str) -> str:
    """
    Abbreviates sports names.
    """
    if isescaped(string):
        return ":" + strip_escape(string)
    return "".join(
        word[0].lower()  # lowercase first letter
        for word in string.split()  # for each word
        if len(word) and word.lower() not in prepositions  # if it is not a preposition
    )


def strip_escape(string: str) -> str:
    """
    Strips escape characters from a string.
    """
    return string.lstrip(":").strip()


def isescaped(string: str) -> bool:
    """
    Checks if a string is an escape character.
    """
    return string.startswith(":")


def normalize_title(string: str) -> str:
    """
    Institutionalizes a school name.
    ---
    capitalize the first letter of each word unless it is
    a preposition or there is a capital letter in the word
    """
    return " ".join(
        map(
            lambda s: (  # TODO: make this not crap
                (s.capitalize() if (s.lower() == s) else s)  # allow for oNeal
                if s.lower() not in prepositions  # lower case it if it is a preposition
                else s.lower()
            ),
            string.split(),  # remove extra spaces
        )
    )


def matchify(string: str) -> str:
    """
    Converts a string to a form without whitespace or caps so it can be
    mathced against a list or set of strings regardless of input case / formatting.
    """
    return "".join(
        map(
            str.lower,
            string.split(),
        )
    )


# TODO: add methods to check if sport, category, and season are valid so they can be
# highlighted in the UI when the user types bad formats. but remember to be
# conservative and only give false when known to be bad. (eg "2" for year)
# or make thses return None if they are bad and return the normalized value if
# they are good.

# === normalize user inputs to shared format ===


def norm_or_pass(normfn: Callable[[str], None | str], text: str) -> str:
    normed = normfn(text)
    if normed is None:
        return text
    else:
        return normed


def normalize_school(school: str) -> None | str:

    if isescaped(school):
        return ":" + strip_escape(school)
    else:
        return normalize_title(school)


def normalize_sports(sport: str) -> None | str:

    # if the starts starts with a colon then only stip (including the space after the colon)
    if isescaped(sport):
        return ":" + strip_escape(sport)

    matchable = matchify(sport)

    # if the sport a value in the known_sport_abbrevs then return the key
    for abbrev, full_name in sport_abrev_to_formal_name.items():
        if matchable in {abbrev, matchify(full_name)}:
            return full_name
    else:
        return None


def normalize_category(raw_cato: str) -> None | str:
    # if the starts starts with a colon then only strip (including the space after the colon)
    if isescaped(raw_cato):
        return ":" + strip_escape(raw_cato)

    matchable = matchify(raw_cato).rstrip("s'").replace(" ", "").replace("-", "")

    for (
        formal,
        variations,
    ) in category_formal_to_variations.items():
        if matchable in variations:
            return formal
    else:
        return None


def normalize_season(season: str) -> None | str:
    return None

    # if season.startswith(":"):
    #     return ":" + season.lstrip(":").strip()

    # end_raw: str | None
    # if "-" in season:
    #     start_raw, end_raw = filter(None, season.split("-"))
    # else:
    #     start_raw, end_raw = season, None

    # start = start_raw.strip()

    # if end_raw is None and len(start) == 4 and start.isnumeric():
    #     return f"{start}-{(int(start)+1)%100:02}"
    # else:
    #     return None
