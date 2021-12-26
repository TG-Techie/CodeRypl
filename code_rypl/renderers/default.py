from __future__ import annotations
from typing import *

from .tools import (
    isescaped,
    strip_escape,
    abbreviate,
    normalize_title,
    remove_prepositions,
    normalize_category,
    sport_abrev_to_formal_name,
    matchify,
    norm_or_pass,
)


SKIPPED_WORDS = {"the", "at", "in", "from", "over", "of", "and"}

GENDER_LUT = {
    "m": {"mens", "men", "m"},
    "w": {"womens", "women", "w"},
    "n": {"nongendered", "nongender", "none", "n"},
}


class SportsAbbreviationError(Exception):
    pass


class SexError(Exception):
    pass


def _strip(st):
    return st.lower().strip().replace("\t", "")


def _strong_strip(st):
    return "".join(st.lower().split())


def abbv_sport(sport: str) -> str:
    """
    Abbreviates a sport name.
    """
    matchable = matchify(sport)
    for abbv, formal in sport_abrev_to_formal_name.items():
        if matchable in {abbv, matchify(formal)}:
            return abbv
    raise SportsAbbreviationError(
        f"{sport!r} is not a valid sport. valid sports are: {', '.join(map(repr,sorted(sport_abrev_to_formal_name.keys())))}"
    )


def abbv_sex(text: str) -> str:

    normed = norm_or_pass(normalize_category, strip_escape(text))

    print(f"{normed=!r}")
    if normed == "Men's":
        return "m"
    elif normed == "women's":
        return "w"
    elif normed == "None":
        return "n"
    else:
        raise SexError(f"unkown sex {text!r}, allowed include men, women, and none")


def abbv_sport(sport: str) -> str:
    """
    Abbreviates a sport name.
    """
    matchable = matchify(sport)
    for abbv, formal in sport_abrev_to_formal_name.items():
        if matchable in {abbv, matchify(formal)}:
            return abbv
    raise SportsAbbreviationError(
        f"{sport!r} is not a valid sport. valid sports are: {', '.join(map(repr,sorted(sport_abrev_to_formal_name.keys())))}"
    )


def abbv_sex(text: str) -> str:

    normed = norm_or_pass(normalize_category, strip_escape(text))

    print(f"{normed=!r}")
    if normed == "Men's":
        return "m"
    elif normed == "women's":
        return "w"
    elif normed == "None":
        return "n"
    else:
        raise SexError(f"unkown sex {text!r}, allowed include men, women, and none")


class RplmFileRenderer:
    def __init__(self, *, school: str, sport: str, category: str, season: str) -> None:

        self.inst_school = inst_school = normalize_title(school)
        self.school_abbv = school_abbv = abbreviate(inst_school)
        self.sport_abbv = sport_abbv = abbv_sport(sport)
        self.sex = sex_abbv = abbv_sex(category)

        self.raw_season = season

        # self.abbv + sex + sport
        self.call = f"{school_abbv}{sex_abbv}{sport_abbv}"

        self.coaches: dict[str, int] = {}

    def suggested_filename(self) -> None | str:
        # TODO(Ryan): Make this a function that return your desired suggested filename
        return f"{self.call}{strip_escape(self.raw_season)}".upper()

    def render_player(self, *, first: str, last: str, num: str, posn: str) -> str:
        """
        returns the output line into the exported  file for the player without newline
        "<call><num>\t<school>'s <pos,> <first> <last> (num), \t<first> <last> (<num>), \t<last>"
        """
        first = strip_escape(first)
        last = strip_escape(last)
        num = strip_escape(num)
        posn = strip_escape(posn)

        # append comma to position if present
        fmtd_posn = f"{posn}, " if len(posn) else ""

        return "\t".join(
            (
                f"{self.call}{num}",
                f"{self.inst_school}'s {fmtd_posn}{first} {last} ({num}), ",
                f"{first} {last} ({num}), ",
                f"{last}",
            )
        )

    def render_coach(self, *, first: str, last: str, kind: str) -> str:
        """
        returns the output line into the exported  file for the coach
        """
        kind_ab = self._kind_abbv(kind)

        return "\t".join(
            (
                f"{self.call}{kind_ab}",
                f"{self.inst_school}'s {kind}, {first} {last}, ",
                f"{first} {last}, ",
                f"{last}",
            )
        )

    def _kind_abbv(self, kind: str) -> str:
        # increment the kind for the next coach or make it 1 if it doesn't exist
        self.coaches[kind] = self.coaches.get(kind, 0) + 1
        # TODO(Ryan): I don't think this does what you want it to do. (~Jay)
        ret = ""
        for item in kind:
            ret += item[0]
        return ret + str(self.coaches[kind])

    # def _call(self, school, sport, sex):
    #     return self.abbv + sex + sport

    def _sex(self, category):
        category = _strong_strip(category).replace("'", "")
        # This is using the dictionary of sets to lookup the sex information.
        for sex, inputs in GENDER_LUT.items():
            if category in inputs:
                return sex
        raise SexError(f"""Got {category!r}, need "men", "women", or "none".""")

    # def _sport(self, sport: str) -> str:
    #     sport = _strong_strip(sport)
    #     if sport in SPORTS_LUT:
    #         return SPORTS_LUT[sport]
    #     raise SportsAbbreviationError(
    #         f"{sport!r} is not a valid option. Please try again. Allowed sports include: {', '.join(SPORTS_LUT.keys())}"
    #     )
