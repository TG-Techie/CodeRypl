from __future__ import annotations
from typing import *


@runtime_checkable
class RplmFileRenderer(Protocol):
    def __init__(self, *, school: str, sport: str, category: str, season: str) -> None:
        ...

    def suggested_filename(self) -> None | str:
        ...

    def render_player(
        self, *, first: str, last: str, num: str, posn: None | str
    ) -> str:
        """
        returns the output line into the exported  file for the player
        """
        ...

    def render_coach(self, *, first: str, last: str, kind: str) -> str:
        """
        returns the output line into the exported  file for the coach
        """
        ...
