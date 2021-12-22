from __future__ import annotations
from typing import *


SPORTS_LUT = {
    "hockey": "hky",
    "basketball": "bball",
    "soccer": "soc",
    "baseball": "baseb",
    "softball": "softb",
    "lacrosse": "lax",
    "football": "fb",
    "fieldhockey": "fhky",
}

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
    return _strip(st).replace(" ", "")


class RplmFileRenderer:
    def __init__(self, *, school: str, sport: str, category: str, season: str) -> None:
        self.school = school
        self.sport = self._sport(sport)
        self.sex = self._sex(category)
        self.abbv = self._abbv(school)
        self.call = self._call(self.school, self.sport, self.sex)
        self.coaches: dict[str, int] = {}

    def suggested_filename(self) -> None | str:
        # TODO(Ryan): Make this a function that return your desired suggested filename
        return "SomeFileName"

    def render_player(self, *, first: str, last: str, num: str, posn: str) -> str:
        """
        returns the output line into the exported  file for the player without newline
        "<call><num>\t<school>'s <pos,> <first> <last> (num), \t<first> <last> (<num>), \t<last>"
        """
        return "\t".join(
            (
                f"{self.call}{num}",
                f"{self.school}'s {(posn+', ')*bool(posn)} {first} {last} ({num}), ",
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
                f"{self.call}{kind_ab}" f"{self.school}'s {kind}, {first} {last}, ",
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

    def _call(self, school, sport, sex):
        return self.abbv + sex + sport

    @staticmethod
    def _abbv(school: str) -> str:

        return "".join(w[0].lower() for w in school.split() if w not in SKIPPED_WORDS)

    def _sex(self, category):
        category = _strong_strip(category).replace("'", "")
        # This is using the dictionary of sets to lookup the sex information.
        for sex, inputs in GENDER_LUT.items():
            if category in inputs:
                return sex
        raise SexError("""Got {category}, need "men", "women", or "none".""")

    def _sport(self, sport: str) -> str:
        sport = _strong_strip(sport)
        if sport in SPORTS_LUT:
            return SPORTS_LUT[sport]
        raise SportsAbbreviationError(
            f"{sport!r} is not a valid option. Please try again. Allowed sports include: {', '.join(SPORTS_LUT.keys())}"
        )
