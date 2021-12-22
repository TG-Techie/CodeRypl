from __future__ import annotations

import sys
import os

from typing import *
from dataclasses import dataclass, field


# import the necessary modules
import PySide6 as pyside
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import (
    Qt,
    # QModelIndex,
    # QAbstractTableModel,
    # QMimeData,
    QEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTabWidget,
    QTextEdit,
    QLabel,
    QTableView,
    QSizePolicy,
    QScrollArea,
    QAbstractItemView,
    QHeaderView,
)


from model import RplmFileModel, Player
from table import RplmTableView

# maybe name this code ryple document?
@final
class CodeRyplWindow(QMainWindow):

    model: RplmFileModel

    @overload
    def __init__(self, model: RplmFileModel) -> None:
        ...

    @overload
    def __init__(self) -> None:
        ...

    def __init__(self, model: None | RplmFileModel = None) -> None:
        # TODO: make this take a filename as an argument and open it
        # or none for an untitled one
        super().__init__()

        self.setFixedSize(720, 450)

        self.init_layout()

        model = RplmFileModel.untitled() if model is None else model
        self._load_model(model)

        self._skip_next_row_forward = False

    def _load_model(self, model: RplmFileModel) -> None:

        self.model = model
        self.setWindowTitle(f"CodeRyple - {model.filename}")

        self.coach_table.load_rplm_model(model.coaches)
        self.player_table.load_rplm_model(model.players)

        self.school_input.setText(model.school)
        self.sport_input.setText(model.sport)
        self.category_input.setText(model.category)
        self.season_input.setText(model.season)

    def init_layout(self) -> None:
        # setup the base widget and layout
        self.base_widget = base_widget = QWidget()
        self.base_layout = base_layout = QVBoxLayout()

        base_widget.setLayout(base_layout)
        self.setCentralWidget(base_widget)

        # the app has three sections, header, metadata, and table
        self.header = header = self._make_header()
        self.metadata = metadata = self._make_metadata()

        self.player_table = player_table = RplmTableView()
        self.coach_table = coach_table = RplmTableView()

        # make a tab widget to hold the tables
        self.tab_widget = tab_widget = QTabWidget()
        tab_widget.addTab(player_table, "Players")
        tab_widget.addTab(coach_table, "Coaches")

        # add the header and table to the layout
        base_layout.addLayout(header)
        base_layout.addLayout(metadata)
        base_layout.addWidget(tab_widget)

        # self.setCentralWidget(table)

    def _make_header(self) -> QHBoxLayout:
        self.header_layout = header_layout = QHBoxLayout()
        # create the open and export buttons and labels
        self.open_button = open_button = QPushButton("Open")
        # self.filename_input = filename_input = QLineEdit(self.model.filename)
        self.export_button = export_button = QPushButton("Export")

        # add the buttons  and current lable to the horizontal layout
        header_layout.addWidget(open_button)
        # header_layout.addWidget(filename_input)
        header_layout.addWidget(export_button)

        return header_layout
    
    def export_file()

    def _make_metadata(self) -> QHBoxLayout:
        # the meta data has four fields:
        # - school
        # - sport
        # - category (sex)
        # - Intended Season

        # each field is a text input with a lable above it
        # the label is left justitied
        # the fields are hoizontally aligned

        self.metalayout = metalayout = QHBoxLayout()

        # make the inputs
        # TODO: make the default values based on teh laoded file_modle
        self.school_input = school_input = QLineEdit("...")
        school_input.setPlaceholderText("School of Name")
        school_input.textEdited.connect(
            lambda: self.model.set_meta(school=school_input.text())
        )

        self.sport_input = sport_input = QLineEdit("...")
        sport_input.setPlaceholderText("SportsBall")
        sport_input.textEdited.connect(
            lambda: self.model.set_meta(sport=sport_input.text())
        )

        self.category_input = category_input = QLineEdit("...")
        category_input.setPlaceholderText("mens, womens, etc")
        category_input.textEdited.connect(
            lambda: self.model.set_meta(category=category_input.text())
        )

        self.season_input = season_input = QLineEdit("...")
        season_input.setPlaceholderText("1701-02")
        season_input.textEdited.connect(
            lambda: self.model.set_meta(season=season_input.text())
        )

        # add the widgets to the layout
        metalayout.addWidget(school_input)
        metalayout.addWidget(sport_input)
        metalayout.addWidget(category_input)
        metalayout.addWidget(season_input)

        return metalayout


class CodeRyplApplication(QApplication):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._windows: list[CodeRyplWindow] = []
        # # the below commented code was auto-suggested by copilot
        # self.setStyle("Fusion")
        # self.setStyleSheet(
        #     open(
        #         os.path.join(os.path.dirname(__file__), "..", "styles", "fusion.qss"),
        #         "r",
        #     ).read()
        # )

    def new_window(self):
        window = CodeRyplWindow()
        self._windows.append(window)
        window.show()
        return window


if __name__ == "__main__":
    app = CodeRyplApplication(sys.argv)
    window = app.new_window()

    sys.exit(app.exec())
