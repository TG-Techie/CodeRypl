from __future__ import annotations

import sys
import pathlib
import time

from typing import *

from .model import RplmFile, RplmList, blocking_popup
from .table import RplmTableView

# import the necessary modules
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMessageBox,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTabWidget,
    QMenuBar,
    QCompleter,
    QStyleFactory,
    QFileDialog,
)

from .renderers import tools as renderer_tools
from .model import Player, Coach
from .table import ColumnCompleterDelegate


UNSAVED_UI_CHECK_INTERVAL = 1000  # milliseconds

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

        self._setup_file_menu()
        self._setup_edit_menu()

    def _setup_file_menu(self) -> None:
        self.file_menu = file_menu = self.addMenu("File")
        file_menu.addAction("New", self.doc.app.new_document, "Ctrl+N")
        file_menu.addAction("Open", self.open_file, "Ctrl+O")
        file_menu.addSeparator()
        # TODO: add open recent
        file_menu.addAction("Save", self.doc.save, "Ctrl+S")
        file_menu.addAction("Save As", self.doc.save_as, "Ctrl+Shift+S")
        file_menu.addSeparator()
        # export
        file_menu.addAction("Export", self.doc.export_replacements, "Ctrl+Shift+E")
        file_menu.addAction("Close", self.doc.close, "Ctrl+W")

    def _setup_edit_menu(self) -> None:
        edit_menu = self.addMenu("Edit")
        # todo: add undo/redo
        edit_menu.addAction(
            "Undo",
            lambda: blocking_popup("Undo not implemented"),
            "Ctrl+Z",
        )
        edit_menu.addAction(
            "Redo",
            lambda: blocking_popup("Redo not implemented"),
            "Ctrl+Shift+Z",
        )
        edit_menu.addAction(
            "About",
            lambda: blocking_popup("About not implemented, but Hi! I'm software."),
        )
        edit_menu.addSeparator()
        # remove empty lines
        edit_menu.addAction(
            "Delete Line",
            # lamdbd so self is captured and not bound to the model item
            lambda: None
            if (table := self.doc.get_focused_table()) is None
            else table.remove_selected_row(),
        )
        edit_menu.addAction("Remove Empty Lines", self.remove_empty_lines)

    def open_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open File", str(self.doc._last_export_path), "RPLM Files (*.rplm)"
        )

        # TODO: add a proper check to see if the file is already open, using app. swithc focus

        if filename in (
            (other_doc := d).model.filename for d in self.doc.app._documents
        ):
            other_doc.switch_focus()
            return

        if filename == "":  # then open canceled
            return
        elif self.doc.model.isempty():
            self.doc.load_file_model(RplmFile.open(filename))
        elif filename:
            self.doc.app.new_document(filename)
        else:
            blocking_popup(f"error opening file {filename!r}")

    def remove_empty_lines(self) -> None:
        self.doc.model.remove_empty_lines()


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

        self.load_file_model(
            RplmFile.untitled() if filename is None else RplmFile.open(filename)
        )

        # file export state
        self._last_export_path = (
            pathlib.Path.home() if filename is None else pathlib.Path(filename).parent
        )

        self._title_refresh_timer = title_refresh_timer = QTimer(self)
        title_refresh_timer.setInterval(UNSAVED_UI_CHECK_INTERVAL)
        title_refresh_timer.timeout.connect(self._title_refresh_handler)
        title_refresh_timer.start()

    def _title_refresh_handler(self):
        self._refresh_title()
        self._title_refresh_timer.start()

    def switch_focus(self) -> None:
        # set focus to this window
        self.app.setActiveWindow(self)
        # move the window to the front
        self.raise_()

    def get_focused_table(self) -> None | RplmTableView:
        if self.coach_table.hasFocus():
            return self.coach_table
        elif self.player_table.hasFocus():
            return self.player_table
        else:
            raise RuntimeError("No table has focus")

    def save(self) -> None:
        """
        if this has been unsaved, save as. otehrwise,
        save to the current file
        """
        if self.model.filename is None:
            self.save_as()
        else:
            self.model.save_to_file(self.model.filename)

    def save_as(self) -> None:

        # resolve the suggested save as name
        if self.model.isempty():
            suggested_filename = "SaveAs"
        else:
            try:
                suggested_filename = self._resolve_suggested_filename(
                    ChosenRenderer(**self.model.meta_as_dict()), "SameAs"
                )
            except Exception as err:
                print(f"Error resolving suggested filename: {err}")
                suggested_filename = "SaveAs"

        # open the file dialog, with a don't save option
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As (.rplm)",
            str(self._last_export_path / f"{suggested_filename}.rplm"),
            "RPLM Files (*.rplm)",
        )

        if filename == "":  # then save canceled
            return

        path = pathlib.Path(filename)

        # TODO: maybe spruce this up?
        try:
            if filename:
                self.model.save_to_file(filename)
        except Exception as e:
            blocking_popup(f"Error saving file({type(e).__name__}): {e}")
            raise e

        # alter the data/rename instead of opening a new file
        name = str(path)
        self.model.filename = name
        self.model.set_as_saved_now()
        self.set_window_title(name)

    def set_window_title(self, title: str) -> None:
        self._title = title.split("/")[-1]
        self._refresh_title()

    def _refresh_title(self) -> None:
        edit_msg = (
            "",
            " - unsaved edits  ",
        )[self.model.changed()]
        self.setWindowTitle(f"CodeRypl - {self._title}{edit_msg}")

    def close(self) -> bool:
        should_close = self._check_for_save_on_close()
        print(f"{should_close=}")
        if should_close:
            return super().close()
        else:
            return False

    def _check_for_save_on_close(self) -> bool:
        if self.model.changed():
            # make a popup to ask if they want to save
            popup = QMessageBox(self)
            popup.setText("Save changes before closing?")
            popup.setStandardButtons(
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            popup.setDefaultButton(QMessageBox.Save)
            popup.setWindowTitle("Unsaved Changes")
            popup.setIcon(QMessageBox.Warning)
            choice = popup.exec()
            # if they choose to save, save
            if choice == QMessageBox.Save:
                self.save()
                return True
            elif choice == QMessageBox.Cancel:
                print("cancel")
                return False
            else:
                double_check = QMessageBox(self)
                double_check.setText(
                    "Are you sure you want to quit and discard all changes?"
                )
                double_check.setStandardButtons(
                    QMessageBox.Cancel | QMessageBox.Discard
                )
                double_check.setWindowTitle("Are you sure?")
                double_check.setDefaultButton(QMessageBox.Cancel)
                double_check.setIcon(QMessageBox.Warning)
                check = double_check.exec()
                if check == QMessageBox.Cancel:
                    return False
                elif check == QMessageBox.Discard:
                    return True
        return False

    def export_replacements(self):
        try:
            renderer = ChosenRenderer(**self.model.meta_as_dict())

            exportname = self._resolve_suggested_filename(renderer, "Untitled") + ".txt"

            # promot the user to select a file
            dialog = QFileDialog(
                caption="Export File (.txt)",
                directory=str(self._last_export_path / exportname),
                filter="text files (*.txt)",
            )
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setDefaultSuffix("txt")
            dialog.exec()
            raw_exportpath = dialog.selectedFiles()[0]

            # raw_exportpath, _ = dialog.getSaveFileName(
            #     self,
            #     caption="Export File (.txt)",
            #     dir=str(self._last_export_path / exportname),
            #     filter="text files (*.txt)",
            # )

            exportpath = pathlib.Path(raw_exportpath)

            # some sanity checks on the export path
            if raw_exportpath in {None, ""}:
                raise ExportError("No file selected")
            if exportpath.exists() and not exportpath.is_file():
                raise ExportError("Export path is not a file, canceling export")
            if exportpath.suffix != ".txt":
                raise ExportError("Export path must end in .txt, canceling export")

            # save it so future exports open at the same location
            self._last_export_path = exportpath.parent

            try:
                # do the actual export!!
                with exportpath.open("w") as file:
                    file.truncate(0)
                    self.model.export_into(file, renderer=renderer)
            except Exception as err:
                blocking_popup(f"Error exporting file({type(err).__name__}): {err}")
                raise err
            else:
                # TODO: consider removing this
                # show a confirmation dialog
                blocking_popup(f"Export Successful!\n" f"(exported to: {exportpath!r})")

        except Exception as e:
            blocking_popup(f"{type(e).__name__}: {e}")
            raise e

    def _resolve_suggested_filename(
        self, renderer: ChosenRenderer, default: str
    ) -> str:
        currentname = self.model.filename
        suggested_name = renderer.suggested_filename()
        if currentname is not None:
            # remove the extension
            return ".".join(currentname.split(".")[:-1])
        elif suggested_name is not None:
            return suggested_name
        else:
            return default

    # === qt / gui setup ===

    def closeEvent(self, event) -> None:
        if self._check_for_save_on_close():
            return super().closeEvent(event)
        else:
            event.ignore()

    def init_layout(self) -> None:
        # setup the base widget and layout
        self.base_widget = base_widget = QWidget()
        self.base_layout = base_layout = QVBoxLayout()

        base_widget.setLayout(base_layout)
        self.setCentralWidget(base_widget)

        # === the header contains the meta data, export button, and save button ===
        self.header = header = QHBoxLayout()
        # this is too long and boring to put right in here
        self.metadata = metadata = self._make_metadata()
        # save button
        self.save_button = save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        # export button
        self.export_button = export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_replacements)
        # add the export button so it is on the right
        header.addLayout(metadata)
        header.addWidget(save_button)
        header.addWidget(export_button)

        # ==== the tables for players and coaches are in a tab view ====
        self.tab_widget = tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.North)
        tab_widget.tabBar().setDocumentMode(True)
        tab_widget.tabBar().setExpanding(True)
        # TODO: make the selected tab color a little better, but fine for now
        tab_widget.tabBar().setStyle(QStyleFactory.create("Fusion"))

        # --- the player table ---
        self.player_table = player_table = RplmTableView(
            Player.num_cols(),
            num_opt_cols=1,
        )
        self.coach_table = coach_table = RplmTableView(
            Coach.num_cols(),
            cols_with_completion={2: ColumnCompleterDelegate},
            num_opt_cols=0,
        )

        # add the tables as tabs
        tab_widget.addTab(player_table, "Players")
        tab_widget.addTab(coach_table, "Coaches")

        # === overal strucutre ===
        base_layout.addLayout(header)
        base_layout.addWidget(tab_widget)

    def _make_metadata(self) -> QHBoxLayout:

        self.metalayout = metalayout = QHBoxLayout()

        # make the inputs
        # TODO: make the default values based on teh laoded file_modle
        self.school_input = school_input = self._make_metatext_input(
            prompt="School of Name",
            normalize=renderer_tools.normalize_school,
            on_change=lambda: self.model.set_meta(school=school_input.text()),
        )

        self.sport_input = sport_input = self._make_metatext_input(
            prompt="SportsBall",
            about_width_of=max(
                renderer_tools.sport_abrev_to_formal_name.values(), key=len
            ),
            suggestions=renderer_tools.sport_abrev_to_formal_name.values(),
            normalize=renderer_tools.normalize_sports,
            on_change=lambda: self.model.set_meta(sport=sport_input.text()),
        )

        self.category_input = category_input = self._make_metatext_input(
            prompt="Men's, Women's, etc",
            about_width_of=":Women's",
            suggestions=renderer_tools.category_formal_to_variations,
            normalize=renderer_tools.normalize_category,
            on_change=lambda: self.model.set_meta(category=category_input.text()),
        )

        this_year = time.localtime().tm_year
        suggested_season = f"{this_year:04}-{(this_year+1)%100:02}"

        self.season_input = season_input = self._make_metatext_input(
            prompt=suggested_season,
            about_width_of=":0000-00",
            normalize=renderer_tools.normalize_season,
            suggestions=[suggested_season, f":{suggested_season}"],
            suggestion_inline=True,
            on_change=lambda: self.model.set_meta(season=season_input.text()),
        )

        # add the widgets to the layout
        metalayout.addWidget(school_input)
        metalayout.addWidget(sport_input)
        metalayout.addWidget(category_input)
        metalayout.addWidget(season_input)

        return metalayout

    def _make_metatext_input(
        self,
        *,
        prompt: str,
        about_width_of: str | None = None,
        on_change: Callable[[], None] | None = None,
        normalize: Callable[[str], None | str] | None = None,
        suggestions: Iterable[str] | None = None,
        suggestion_inline: bool = False,
    ) -> QLineEdit:

        widget = QLineEdit("")
        metrics = QFontMetrics(widget.font())
        widget.setPlaceholderText(prompt)
        widget.setFixedHeight(int(metrics.height() * 2))

        widget.setStyleSheet("QLineEdit { border-radius: 5%; }")

        if about_width_of is not None:
            widget.setFixedWidth(
                int(
                    QFontMetrics(widget.font()).boundingRect(about_width_of).width()
                    * 1.25
                )
            )

        if on_change is not None:
            # use textChanged so it saves to the model on every keystroke
            widget.textChanged.connect(on_change)

        if normalize is not None:

            widget.editingFinished.connect(
                lambda: widget.setText(
                    renderer_tools.norm_or_pass(normalize, widget.text())
                )
            )

        if suggestions is not None:
            # make a completer
            completer = QCompleter(list(suggestions))
            # set the completer to be case insensitive
            completer.setCaseSensitivity(Qt.CaseInsensitive)

            # make the complete show on focus
            if suggestion_inline:
                completer.setCompletionMode(QCompleter.InlineCompletion)
                completer.setFilterMode(Qt.MatchStartsWith)
            else:
                completer.setCompletionMode(QCompleter.PopupCompletion)
                completer.setFilterMode(Qt.MatchContains)

            # TODO: to show the completer on focus override the focusChanged method
            # on the app and pass a callback down to this
            # (or something like enviroment variable)

            # set the completer
            widget.setCompleter(completer)

        return widget

    def load_file_model(self, model: RplmFile) -> None:

        self.model = model
        self.set_window_title(
            "Untitled.rplm" if model.filename is None else model.filename
        )

        self.coach_table.load_rplm_list(model.coaches)
        self.player_table.load_rplm_list(model.players)

        if len(model.school):
            self.school_input.setText(model.school)
        if len(model.sport):
            self.sport_input.setText(model.sport)
        if len(model.category):
            self.category_input.setText(model.category)
        if len(model.season):
            self.season_input.setText(model.season)
