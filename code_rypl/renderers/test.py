from __future__ import annotations
from typing import *


class RplmFileRenderer:
    def __init__(self, *, school: str, sport: str, category: str, season: str) -> None:
        print(
            f"{self.__class__.__name__}.__init__({school=}, {sport=}, {category=}, {season=})"
        )

    def suggested_filename(self) -> None | str:
        return None

    def render_player(self, *, first: str, last: str, num: str, posn: str) -> str:
        """
        returns the output line into the exported  file for the player
        """
        print(
            f"{self.__class__.__name__}.render_player({first=}, {last=}, {num=}, {posn=})"
        )
        return "\t".join((first, last, num, posn))

    def render_coach(self, *, first: str, last: str, kind: str) -> str:
        """
        returns the output line into the exported  file for the coach
        """
        print(f"{self.__class__.__name__}.render_coach({first=}, {last=}, {kind=})")
        return "\t".join((first, last, kind))
