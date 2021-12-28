from __future__ import annotations

import sys
from typing import *

from .model import *

from PySide6.QtCore import (
    Qt,
    QEvent,
    QObject,
)

from PySide6.QtWidgets import (
    QTableView,
    QSizePolicy,
    QAbstractItemView,
    QHeaderView,
    QStyledItemDelegate,
    QLineEdit,
    QCompleter,
)

# cli args imports
ENABLE_STAY_ON_INSERT_ABOVE = not (
    {"--disable-stay-on-above-insert", "-dis-soai"} & set(sys.argv)
)
ENABLE_MOVE_TO_FIRST_ON_INSERT = not (
    {"--disable-move-to-first-on-insert", "-dis-mtfoi"} & set(sys.argv)
)
# DISABLE_TAB_WRAP = bool({"--disable-tab-wrap", "-dis-tw"} & set(sys.argv))


class ColumnItemDeleagate(QStyledItemDelegate):
    def __init__(self, table: QTableView, *args: Any, **kwargs: Any) -> None:
        self._table = table
        return super().__init__(table, *args, **kwargs)


class ColumnCompleter(QCompleter):
    def __init__(
        self,
        completions: Sequence[str],
        parent: Optional[QObject] = None,
    ) -> None:
        self._completions = completions
        super().__init__(completions, parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)

        self.setFilterMode(Qt.MatchStartsWith)
        # self.setCompletionMode(QCompleter.InlineCompletion)
        # self.setFilterMode(Qt.MatchContains)
        self.setCompletionMode(QCompleter.PopupCompletion)


class ColumnCompleterDelegate(ColumnItemDeleagate):
    preloaded: ClassVar[set[str]] = set()

    def createEditor(self, parent, option, index):

        self.editor = editor = QLineEdit(parent)

        editor.installEventFilter(self._table)

        completions = (
            self._table._rplm_list.get_col_set(index.column()) | self.preloaded
        )

        completer = ColumnCompleter(completions, parent)

        editor.setCompleter(completer)
        return editor


class CoachItemDelegate(ColumnCompleterDelegate):
    preloaded = {
        "Head Coach",
        "assistant Coach",
        "associate Coach",
        "assistant head coach",
        "associate head coach",
        "athletic trainer",
        "goalie coach",
        "strength and conditioning coach",
    }


class RplmTableView(QTableView):
    def __init__(
        self,
        num_cols: int,
        num_opt_cols: int,  # optional arguments will never not be at end
        cols_with_completion: dict[int, Type[QStyledItemDelegate]] = {},
    ) -> None:
        super().__init__(parent=None)
        # self._model: None | RplmFileModel = None

        self._num_cols = num_cols

        # generate indices where enter is allowed to start a newline
        self._optional_cols = {num_cols - (i + 1) for i in range(num_opt_cols + 1)}

        for col, delegate_type in cols_with_completion.items():
            assert col < num_cols, f"col {col} is out of range, has to be < {num_cols}"
            self.setItemDelegateForColumn(col, delegate_type(self))

        self._init_format()

        # navigation state
        self._skip_next_row_forward = False

    def load_rplm_list(self, rplm_ls: RplmList) -> None:
        self._rplm_list = rplm_ls
        rplm_ls.set_selected_cell = self.setCurrentIndex
        self.setModel(rplm_ls)

    def _init_format(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # copilot suggested code
        # self.setStyleSheet("QTableView {selection-background-color: #f0f0f0;}")

        self.setDragDropMode(QAbstractItemView.DragDrop)

        # hide the verical and horizontal headers
        self.verticalHeader().hide()
        self.horizontalHeader().hide()

        # set the column widths to be the same as the header
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.installEventFilter(self)

    def insert_above(self) -> None:

        index = self.currentIndex()

        self._rplm_list.insert(index.row(), Player.empty())
        self._skip_next_row_forward = True and ENABLE_STAY_ON_INSERT_ABOVE

        if ENABLE_MOVE_TO_FIRST_ON_INSERT:
            self.setCurrentIndex(index.siblingAtColumn(0))

    def insert_below(self) -> None:

        index = self.currentIndex()

        self._rplm_list.insert(index.row() + 1, Player.empty())
        self.setCurrentIndex(
            index.sibling(
                (index.row() + 1) % len(self._rplm_list),
                0 if ENABLE_MOVE_TO_FIRST_ON_INSERT else index.column(),
            )
        )

    # table navigation methods
    def move_right(self):
        index = self.currentIndex()
        self.setCurrentIndex(
            index.siblingAtColumn((index.column() + 1) % Player.num_cols())
        )

    def move_left(self):
        index = self.currentIndex()
        self.setCurrentIndex(
            index.siblingAtColumn((index.column() - 1) % Player.num_cols())
        )

    # def _move_to_first_row(self, index: QModelIndex):
    #     self.setCurrentIndex(index.siblingAtRow(0))

    # def _move_to_last_row(self, index: QModelIndex):
    #     self.rrentIndex(index.siblingAtRow(len(self._model) - 1))

    def move_down(self):
        index = self.currentIndex()
        self.setCurrentIndex(
            index.siblingAtRow((index.row() + 1) % len(self._rplm_list))
        )

    def move_up(self):
        index = self.currentIndex()
        self.setCurrentIndex(
            index.siblingAtRow((index.row() - 1) % len(self._rplm_list))
        )

    def go_col(self, col: int):
        index = self.currentIndex()
        self.setCurrentIndex(index.siblingAtColumn(col))

    def go(self, row: int, col: int):
        index = self.currentIndex()
        self.setCurrentIndex(
            index.sibling(row % len(self._rplm_list), col % Player.num_cols())
        )

    def remove_row(self, row: int):
        self._rplm_list.pop(row)
        self.go_col(0)

    def remove_selected_row(self):
        index = self.currentIndex()
        self.remove_row(index.row())

    def eventFilter(self, _, event) -> bool:

        index = self.currentIndex()

        # input sanitation
        if not index.isValid() or event.type() != QEvent.KeyPress:
            return False

        is_enter = event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return
        is_tab = event.key() == Qt.Key_Tab
        is_backtab = event.key() == Qt.Key_Backtab
        is_delete = event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace
        is_escape = event.key() == Qt.Key_Escape

        with_shift = event.modifiers() & Qt.ShiftModifier
        with_control = event.modifiers() & Qt.MetaModifier
        with_option = event.modifiers() & Qt.AltModifier

        at_bottom = index.row() == len(self._rplm_list) - 1
        in_opt_col = index.column() in self._optional_cols
        at_last_col = index.column() == self._num_cols - 1

        # TODO: above line needs to be two variables for proper tab/enter behavior
        row_empty = self._rplm_list.get_rplm(index.row()).isempty()
        cell_was_empty = (
            self._rplm_list.get_rplm_field(index.row(), index.column()) == ""
        )
        if is_tab:
            print("tab")

        if is_delete and with_shift:
            self.remove_selected_row()
            return True
        elif is_delete:
            self._rplm_list.get_rplm(index.row()).set_col(index.column(), "")
            self._rplm_list.refresh()
            return True
        elif is_tab and at_bottom and at_last_col:
            if row_empty:
                self.go_col(0)
            else:
                self.insert_below()
            return True
        if is_tab and at_last_col:
            if row_empty:
                self.go_col(0)
            else:
                self.go(index.row() + 1, 0)
            return True
        elif is_tab:
            self.move_right()
            return True
        elif is_backtab:
            self.move_left()
            return True
        elif is_enter:
            if with_shift and with_option:
                self.insert_above()
                return False
            elif with_shift:
                self.move_up()
                return True
            elif with_option:
                self.insert_below()
                return True
            elif at_bottom and in_opt_col:
                if row_empty:
                    self.go_col(0)
                else:
                    self.insert_below()
                return True
            elif in_opt_col:
                self.move_down()
                self.go_col(0)
                return True
            if row_empty and at_bottom:
                return True
            else:
                # this gate prenet an enter down after an insert into a row above
                if self._skip_next_row_forward and ENABLE_STAY_ON_INSERT_ABOVE:
                    self._skip_next_row_forward = False
                else:
                    self.move_down()
                return True

        else:
            return False

        # This should be unreachable (also grayed out with pylance)
        assert False, "unreachable"
