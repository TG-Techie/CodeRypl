from __future__ import annotations

from typing import *
from io import StringIO


from ..model import Player, Coach


class InputParser:
    def __init__(self, contents: str) -> None:
        pass

    def school(self) -> None | str:
        return None

    def sport(self) -> None | str:
        return None

    def category(self) -> None | str:
        return None

    def season(self) -> None | str:
        return None

    def parse_players(self) -> Iterable[Player]:
        raise NotImplementedError

    def parse_coaches(self) -> Iterable[Coach]:
        raise NotImplementedError
