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
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTabWidget,
    QTabBar,
    QTextEdit,
    QLabel,
    QTableView,
    QSizePolicy,
    QScrollArea,
    QAbstractItemView,
    QHeaderView,
)


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


# maybe name this code ryple document?
@final
class CodeRyplDocumentWindow(QMainWindow):

    model: RplmFile

    @overload
    def __init__(self, model: RplmFile) -> None:
        ...

    @overload
    def __init__(self) -> None:
        ...

    def __init__(self, model: None | RplmFile = None) -> None:
        # TODO: make this take a filename as an argument and open it
        # or none for an untitled one
        super().__init__()

        self.setFixedSize(720, 450)

        self.init_layout()

        model = RplmFile.untitled() if model is None else model
        self._load_model(model)

        # file export state
        self._last_export_path = pathlib.Path.home()

    def _load_model(self, model: RplmFile) -> None:

        self.model = model
        self.setWindowTitle(
            f"CodeRyple - {'Untitled' if model.filename is None else model.filename}"
        )

        self.coach_table.load_rplm_model(model.coaches)
        self.player_table.load_rplm_model(model.players)

        self.school_input.setText(model.school)
        self.sport_input.setText(model.sport)
        self.category_input.setText(model.category)
        self.season_input.setText(model.season)

    def export_replacements(self):
        try:
            renderer = ChosenRenderer(**self.model.meta_as_dict())

            exportname = self.model.filename
            if exportname is None:
                exportname = renderer.suggested_filename()
            if exportname is None:
                exportname = "Untitled"

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


class CodeRyplApplication(QApplication):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._windows: list[CodeRyplDocumentWindow] = []
        # # the below commented code was auto-suggested by copilot
        # self.setStyle("Fusion")
        # self.setStyleSheet(
        #     open(
        #         os.path.join(os.path.dirname(__file__), "..", "styles", "fusion.qss"),
        #         "r",
        #     ).read()
        # )

    def new_window(self):
        window = CodeRyplDocumentWindow()
        self._windows.append(window)
        window.show()
        return window


def run_main() -> NoReturn:
    app = CodeRyplApplication(sys.argv)
    window = app.new_window()

    sys.exit(app.exec())
