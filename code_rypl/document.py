from __future__ import annotations

import sys
import pathlib

from typing import *

from .model import RplmFile, RplmList, blocking_popup
from .table import RplmTableView

# import the necessary modules
import PySide6 as pyside
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QFontMetrics

from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTabWidget,
    QMenuBar,
)

if TYPE_CHECKING:
    from .app import CodeRyplApplication

# parse the command line arguments
renderer_args = {arg.split("=")[1] for arg in sys.argv if arg.startswith("--renderer=")}
assert len(renderer_args) <= 1, "Only one renderer can be specified"
if len(renderer_args) == 0:
    renderer_name = "default"
else:
    (renderer_name,) = renderer_args

if renderer_name == "default":
    from .renderers.default import RplmFileRenderer as ChosenRenderer  # type: ignore
elif renderer_name == "test":
    from .renderers.test import RplmFileRenderer as ChosenRenderer  # type: ignore
else:
    raise NotImplementedError(
        f"cutom renderers not implemented yet, got `--renderer={renderer_name}`"
    )


# class TwoFullTabWidget(QTabWidget):
#     def showEvent(self, event: QtGui.QShowEvent) -> None:
#         super().showEvent(event)
#         print(self.styleSheet())
#         self.setStyleSheet(f"QTabBar::tab {{\n\twidth: {self.width()//2 - 24}px;\n}}")
#         print(self.styleSheet())


class ExportError(Exception):
    pass


class CodeRyplMenuBar(QMenuBar):
    def __init__(self, doc: CodeRyplDocumentWindow) -> None:
        super().__init__()

        self.doc = doc

        self.file_menu = file_menu = self.addMenu("File")
        file_menu.addAction("new", self.doc.app.new_document)
        file_menu.addAction("Open", self.open_file)
        # TODO: add open recent
        file_menu.addAction("Save", self.doc.save)
        file_menu.addAction("Save As", self.doc.save_as)
        file_menu.addAction("Export", self.doc.export_replacements)
        file_menu.addAction("Close", self.doc.close)

        # TODO: add an edit meu for removing blank lines, etc.

    def open_file(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File", "", "RPLM Files (*.rplm)"
        )

        # TODO: add a check to see if the file is already open, etc. and use pathlib.Path
        if filename:
            self.doc.app.new_document(filename)


# maybe name this code ryple document?
class CodeRyplDocumentWindow(QMainWindow):

    model: RplmFile

    def __init__(self, app: CodeRyplApplication, filename: None | str = None) -> None:
        # TODO: make this take a filename as an argument and open it
        # or none for an untitled one
        super().__init__()

        self.app = app

        self.setFixedSize(720, 450)

        self.menu_bar = menu_bar = CodeRyplMenuBar(self)
        self.setMenuBar(menu_bar)

        self.init_layout()

        model = RplmFile.untitled() if filename is None else RplmFile.open(filename)
        self._load_model(model)

        # file export state
        self._last_export_path = (
            pathlib.Path.home() if filename is None else pathlib.Path(filename).parent
        )

    def _load_model(self, model: RplmFile) -> None:

        self.model = model
        self.setWindowTitle(
            f"CodeRyple - {'Untitled.rplm' if model.filename is None else model.filename}"
        )

        self.coach_table.load_rplm_model(model.coaches)
        self.player_table.load_rplm_model(model.players)

        self.school_input.setText(model.school)
        self.sport_input.setText(model.sport)
        self.category_input.setText(model.category)
        self.season_input.setText(model.season)

    def save(self) -> None:
        if self.model.filename is None:
            self.save_as()
        else:
            self.model.save_to_file(self.model.filename)

    def save_as(self) -> None:
        # open the file dialog
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save File As",
            str(self._last_export_path / "SaveAs.rplm"),
            "RPLM Files (*.rplm)",
        )

        path = pathlib.Path(filename)

        try:
            if filename:
                self.model.save_to_file(filename)
        except Exception as e:
            blocking_popup(f"Error saving file({type(e).__name__}): {e}")
            raise e

        self.rename(".".join(path.name.split(".")[:-1]))

    def rename(self, name: str) -> None:
        self.model.filename = name
        self.setWindowTitle(f"CodeRyple - {name}")

    def close(self) -> bool:
        self.save()
        return super().close()

    def export_replacements(self):
        try:
            renderer = ChosenRenderer(**self.model.meta_as_dict())

            exportname = self.model.filename
            if exportname is None:
                exportname = renderer.suggested_filename()
            if exportname is None:
                exportname = "Untitled.rplm"

            raw_exportpath, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                caption="Export File",
                dir=str(self._last_export_path / exportname),
                filter="text files (*.txt)",
            )

            exportpath = pathlib.Path(raw_exportpath)

            if raw_exportpath in {None, ""}:
                raise ExportError("No file selected")

            if exportpath.exists() and not exportpath.is_file():
                raise ExportError("Export path is not a file")

            if exportpath.suffix != ".txt":
                raise ExportError("Export path must end in .txt")

            self._last_export_path = exportpath.parent

            with exportpath.open("w") as file:
                file.truncate(0)
                self.model.export_into(file, renderer=renderer)

            blocking_popup(f"Export Successful!\n" f"(exported to: {exportpath!r})")

        except Exception as e:
            blocking_popup(f"{type(e).__name__}: {e}")
            raise e

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
        tab_widget.setTabPosition(QTabWidget.North)
        tab_widget.tabBar().setDocumentMode(True)
        tab_widget.tabBar().setExpanding(True)

        # TODO: make the selected tab color a little better, but fine for now
        tab_widget.tabBar().setStyle(QtWidgets.QStyleFactory.create("Fusion"))

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

        # connect the buttons to the actions
        export_button.clicked.connect(self.export_replacements)

        # add the buttons  and current lable to the horizontal layout
        header_layout.addWidget(open_button)
        # header_layout.addWidget(filename_input)
        header_layout.addWidget(export_button)

        return header_layout

    def _make_metadata(self) -> QHBoxLayout:

        self.metalayout = metalayout = QHBoxLayout()

        # make the inputs
        # TODO: make the default values based on teh laoded file_modle
        self.school_input = school_input = QLineEdit("")
        school_input.setPlaceholderText("School of Name")
        school_input.setFixedHeight(
            int(QFontMetrics(school_input.font()).height() * 1.8)
        )
        school_input.textEdited.connect(
            lambda: self.model.set_meta(school=school_input.text())
        )

        self.sport_input = sport_input = QLineEdit("")
        sport_input.setPlaceholderText("SportsBall")
        sport_input.setFixedHeight(int(QFontMetrics(sport_input.font()).height() * 1.8))
        sport_input.textEdited.connect(
            lambda: self.model.set_meta(sport=sport_input.text())
        )

        self.category_input = category_input = QLineEdit("")
        category_input.setPlaceholderText("mens, womens, etc")
        category_input.setFixedHeight(
            int(QFontMetrics(category_input.font()).height() * 1.8)
        )
        category_input.textEdited.connect(
            lambda: self.model.set_meta(category=category_input.text())
        )

        self.season_input = season_input = QLineEdit("")
        season_input.setPlaceholderText("year")
        season_input.setFixedHeight(
            int(QFontMetrics(season_input.font()).height() * 1.8)
        )
        season_input.textEdited.connect(
            lambda: self.model.set_meta(season=season_input.text())
        )

        # add the widgets to the layout
        metalayout.addWidget(school_input)
        metalayout.addWidget(sport_input)
        metalayout.addWidget(category_input)
        metalayout.addWidget(season_input)

        return metalayout
