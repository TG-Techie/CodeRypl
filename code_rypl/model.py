from __future__ import annotations

import sys
from typing import *
from typing import TextIO, BinaryIO

import pathlib
import msgpack  # type: ignore[import]

from .renderers.template import RplmFileRenderer

from PySide6 import QtGui

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QByteArray,
    QMimeData,
)

from PySide6.QtWidgets import (
    QMessageBox,
)

# TODO: move this into a separate file for ui logic?
# or.... only let it be used in the main window vie catching raised errors.
# consider making a custom exeption for this? it could wrap the original error or a str
def blocking_popup(message):
    msgbox = QMessageBox()
    msgbox.setText(message)
    msgbox.exec()


R = TypeVar("R", bound="Rplm")


class Rplm:

    field_spec: ClassVar[dict[str, int]]
    _cols: dict[int, str]

    def __new__(cls, *args, **kwargs):
        if cls is Rplm:
            raise TypeError("cannot instantiate abstract class Rplm")
        return object.__new__(cls)

    def __init__(self, **kwargs: str) -> None:

        spec = self.field_spec

        assert (
            len(extras := set(kwargs) - set(spec)) == 0
        ), f"unexpedted kwargs: {extras}"

        assert (
            len(missing := set(spec) - set(kwargs)) == 0
        ), f"missing kwargs: {missing}"

        assert set(spec) == set(kwargs), (
            f"argument errors, got {set(kwargs)}, "
            "however this assert should not have been reached, please report this bug"
        )

        self._cols = {spec[f]: kwargs[f] for f in kwargs}

    @classmethod
    def from_cols(self: Type[R], *args: str) -> R:
        assert len(args) == len(
            self.field_spec
        ), f"expected {len(self.field_spec)}, got {len(args)}"
        return self(**{f: args[col] for f, col in self.field_spec.items()})

    def as_cols(self) -> tuple[str, ...]:
        return tuple(self._cols[col] for col in range(self.num_cols()))

    def get_col(self, col: int) -> str:
        return self._cols[col]

    def set_col(self, col: int, value: str) -> None:
        self._cols[col] = value

    def field(self, name: str) -> str:
        return self._cols[self.field_spec[name]]

    def as_fields(self) -> dict[str, str]:
        return {f: self.field(f) for f in self.field_spec}

    def isempty(self) -> bool:
        return set(self._cols.values()) == {""}

    @classmethod
    def empty(cls: Type[R]) -> R:
        return cls(**{f: "" for f in cls.field_spec})

    @classmethod
    def num_cols(cls) -> int:
        return len(cls.field_spec)  # type: ignore

    @classmethod
    def prompt_for_col(cls, col: int) -> str:
        for prompt, colno in cls.field_spec.items():
            if colno == col:
                return prompt
        raise RuntimeError(f"unknown column {col} for {cls.__name__}")


class Player(Rplm):

    # TODO: make this a tuple
    field_spec = dict(
        first=0,
        last=1,
        num=2,
        posn=3,
    )


class Coach(Rplm):

    field_spec = dict(
        first=0,
        last=1,
        kind=2,
    )


class MetaAsDict(TypedDict):
    school: str
    sport: str
    category: str
    season: str


class PlayerAsDict(TypedDict):
    first: str
    last: str
    num: str
    posn: str


class CoachAsDict(TypedDict):
    first: str
    last: str
    kind: str


class SaveDict(TypedDict):
    meta: MetaAsDict
    players: tuple[PlayerAsDict, ...]
    coaches: tuple[CoachAsDict, ...]


class RplmFile:

    metadata_spec: ClassVar[set[str]] = {"school", "sport", "category", "season"}

    def __init__(
        self,
        *,
        filename: None | str = None,
        school: str = "",
        sport: str = "",
        category: str = "",
        season: str = "",
        players: Iterable[Player] | None = None,
        coaches: Iterable[Coach] | None = None,
        set_selected_cell: Callable[[QModelIndex], None] = None,
    ) -> None:
        super().__init__()

        self.players = players = (
            RplmList([Player.empty()]) if players is None else RplmList(players)
        )
        self.coaches = coaches = (
            RplmList([Coach.empty()]) if coaches is None else RplmList(coaches)
        )

        self.school = school
        self.sport = sport
        self.category = category
        self.season = season

        self.filename = filename

        # TODO: store a hash of the last saved file contents here
        # self._last_save: int = None
        self._last_used_index = QModelIndex()

        # intentionally  using the set_selected_cell setter not the internal attribute
        self.set_selected_cell = (
            set_selected_cell if set_selected_cell is not None else (lambda _: None)
        )

    @property
    def set_selected_cell(self) -> Callable[[QModelIndex], None]:
        return self._set_selected_cell

    @set_selected_cell.setter
    def set_selected_cell(self, set_selected_cell: Callable[[QModelIndex], None]):
        self._set_selected_cell = set_selected_cell
        self.players.set_selected_cell = set_selected_cell
        self.coaches.set_selected_cell = set_selected_cell

    @classmethod
    def open(cls, filename: str) -> RplmFile:
        path = pathlib.Path(filename)
        assert path.exists(), f"{filename} does not exist"
        assert path.is_file(), f"{filename} is not a file"
        assert path.suffix == ".rplm", f"{filename} is not a .rplm file"

        with path.open("rb") as file:
            return cls._from_file(file)

    def save_to_file(self, filename: str) -> None:
        path = pathlib.Path(filename)

        if path.exists():
            assert path.is_file(), f"{filename} is not a file"

        assert path.suffix == ".rplm", f"{filename} is not a .rplm file"

        if path.exists():
            blocking_popup(f"{filename} already exists, overwriting")

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as file:
            file.truncate(0)
            self._into_file(file)

    def _into_file(self, into: BinaryIO) -> None:
        data = self._to_save_dict()
        # TODO: add hash to see if the file has changed
        msgpack.pack(data, into)

    def _to_save_dict(self) -> SaveDict:
        return SaveDict(
            meta=self.meta_as_dict(),
            players=tuple(p.as_fields() for p in self.players),  # type: ignore
            coaches=tuple(c.as_fields() for c in self.coaches),  # type: ignore
        )

    @classmethod
    def _from_file(cls, file: BinaryIO) -> RplmFile:

        data = msgpack.unpack(file)

        # validate the data

        # check for missing keys
        assert "meta" in data, f"missing meta section in {file}"
        meta: MetaAsDict = data["meta"]

        # check all the meta fields are present
        assert set(meta) == set(
            cls.metadata_spec
        ), f"missing meta fields: {set(cls.metadata_spec) - set(meta)}"

        assert "players" in data, f"missing players section in {file}"
        players: list[PlayerAsDict] = data["players"]

        assert "coaches" in data, f"missing coaches section in {file}"
        coaches: List[CoachAsDict] = data["coaches"]

        return cls(
            **meta,
            players=(Player(**p) for p in players),
            coaches=(Coach(**c) for c in coaches),
            filename=file.name,
        )

    @classmethod
    def untitled(cls) -> RplmFile:
        return cls(filename=None)

    def isempty(self) -> bool:
        return (
            self.players.isempty()
            and self.coaches.isempty()
            and set(m.strip() for m in self.meta_as_dict().values()) == {""}  # type: ignore
        )

    def meta_as_dict(self) -> MetaAsDict:
        return dict(
            school=self.school,
            sport=self.sport,
            category=self.category,
            season=self.season,
        )

    def set_meta(
        self,
        school: None | str = None,
        sport: None | str = None,
        category: None | str = None,
        season: None | str = None,
    ):
        if school is not None:
            self.school = school
        if sport is not None:
            self.sport = sport
        if category is not None:
            self.category = category
        if season is not None:
            self.season = season

    def export_into(self, file: TextIO, *, renderer: RplmFileRenderer) -> None:

        file.writelines(
            renderer.render_player(**player.as_fields()) + "\n"
            for player in self.players
            if not player.isempty()
        )

        file.writelines(
            renderer.render_coach(**coaches.as_fields()) + "\n"
            for coaches in self.coaches
            if not coaches.isempty()
        )

    def remove_empty_lines(self) -> None:
        self.players.remove_empty_lines()
        self.coaches.remove_empty_lines()


class RplmList(Generic[R], QAbstractTableModel):
    def __init__(
        self,
        data: Iterable[R],
        set_selected_cell: Callable[[QModelIndex], None] = None,
    ):
        super().__init__()

        self._data = list(data)
        assert len(self._data) > 0, f"cannot create an empty RplmList"

        self._data_type = type(self._data[0])

        # live settable attr
        self.set_selected_cell: Callable[[QModelIndex], None] = (
            (lambda _: None) if set_selected_cell is None else set_selected_cell
        )

    def __len__(self) -> int:
        return len(self._data)

    def __str__(self) -> str:
        return f"{type(self).__name__}[{self._data_type.__name__}](...)"

    def __iter__(self) -> Iterator[R]:
        return iter(self._data)

    def current_rplm(self) -> R:
        return self._data[self._last_used_index.row()]

    # QT interface methods
    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        return self._data_type.num_cols()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):  # type: ignore

        # print(f"{self}.data({index}, {role})")

        if not index.isValid():
            return None

        self._last_used_index = index

        rplm = self._data[index.row()]
        value = rplm.get_col(index.column())

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return (
                value if len(value) else self._data_type.prompt_for_col(index.column())
            )

        elif role == Qt.ForegroundRole:
            return None if len(value) else QtGui.QColor("gray")

        return None

    def setData(self, index, value, role):

        self._last_used_index = index
        if role == Qt.EditRole:
            self.set_rplm_field(index.row(), index.column(), value)
            return True
        else:
            raise ValueError(f"{self}.setData({index=}, {value=}, {role=})")

    def get_rplm_field(self, row: int, col: int) -> str:
        return self._data[row].get_col(col)

    def get_rplm(self, row: int) -> R:
        return self._data[row]

    def set_rplm_field(self, row: int, col: int, value) -> None:

        value = value.strip()

        if value == self._data_type.prompt_for_col(col):
            value = ""

        rplm = self._data[row]

        rplm.set_col(col, value)

    def append(self, rplm: R):
        self._data.append(rplm)
        self.refresh()
        # self.set_selected_row(self._last_used_index.siblingAtRow(len(self._data) - 1))

    def insert(self, row: int, rplm: R) -> None:
        self._data.insert(row, rplm)
        self.refresh()

    def refresh(self) -> None:
        self.layoutChanged.emit()

    def pop(self, row: int) -> R:
        item = self._data.pop(row)
        if len(self._data) == 0:
            self.append(self._data_type.empty())  # type: ignore
        self.refresh()
        return item

    def remove_empty_lines(self) -> None:
        self._data = [r for r in self._data if not r.isempty()]
        self.refresh()

    # === qt / ui interface ===

    def flags(self, index):
        return (
            Qt.ItemIsSelectable
            | Qt.ItemIsEnabled
            | Qt.ItemIsEditable
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsDropEnabled
        )

    def mimeData(self, indicies: list[QModelIndex]) -> QMimeData:  # type: ignore
        self._drop_sources = indicies

        if len(indicies) != 1:
            blocking_popup(
                f"Can only drag one item at a time, not {len(indicies)}.\n"
                "(If you're Ryan reading this message, what would that even do?)"
            )

        data = super().mimeData(indicies)  # type: ignore

        data.setData(
            "application/rplm-row",
            QByteArray((str(indicies[0].row())).encode()),
        )
        data.setData(
            "application/rplm-col",
            QByteArray((str(indicies[0].column())).encode()),
        )
        return data

    def dropMimeData(self, data: QMimeData, action, _r, _c, parent):

        if action == Qt.CopyAction:
            dest_pos = (parent.row(), parent.column())
            src_pos = (
                int(data.data("application/rplm-row")),
                int(data.data("application/rplm-col")),
            )

            # swap the fields
            src_value = self.get_rplm_field(*src_pos)
            dest_value = self.get_rplm_field(*dest_pos)

            self.set_rplm_field(*dest_pos, src_value)
            self.set_rplm_field(*src_pos, dest_value)

            # update the table
            self.refresh()

            # keep focus on the dragged item (feels a bit more natural)
            self.set_selected_cell(parent)
        else:
            raise RuntimeError(
                f"unknown drop action {action} in {type(self).__name__}.dropMimeData"
            )

        return True
