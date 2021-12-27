from __future__ import annotations
from typing import *

from PySide6.QtCore import (
    Qt,
    QEvent,
    QObject,
)

from PySide6.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QMainWindow,
    QWidget,
    QMessageBox,
    QDialog,
    QSizePolicy,
)

if TYPE_CHECKING:
    from .app import CodeRyplApplication


class PrefWindow(QMainWindow):
    def __init__(self, app: CodeRyplApplication) -> None:

        super().__init__()

        self.app = app

        self.setWindowTitle("Preferences")
        self.setWindowFlags(Qt.Window)

        self.init_layout()

    def switch_focus(self) -> None:
        # set focus to this window
        self.app.setActiveWindow(self)
        # move the window to the front
        self.raise_()

    def init_layout(self) -> None:
        # make a tab view for about, product info, activation, etc.

        self.base_widget = base_widget = QWidget()
        self.base_layout = base_layout = QVBoxLayout()

        base_widget.setLayout(base_layout)
        self.setCentralWidget(base_widget)

        self.tab_widget = tab_widget = QTabWidget()
        base_layout.addWidget(tab_widget)
        # self.setCentralWidget(tabe_widget)

        # add tabs
        self.init_tab_about()
        self.init_tab_product_info()
        self.init_tab_activation()
        # self.init_tab_advanced()

    def init_tab_about(self) -> None:
        self.about_widget = about_widget = QWidget()
        about_widget.setLayout(QVBoxLayout())
        about_widget.layout().addWidget(
            QMessageBox(
                QMessageBox.Information,
                "About",
                "This is the about tab",
            )
        )
        self.tab_widget.addTab(about_widget, "About")

    def init_tab_product_info(self) -> None:
        self.product_info_widget = product_info_widget = QWidget()
        product_info_widget.setLayout(QVBoxLayout())
        product_info_widget.layout().addWidget(
            QMessageBox(
                QMessageBox.Information,
                "About",
                "This is the product info tab",
            )
        )
        self.tab_widget.addTab(product_info_widget, "Product Info")

    def init_tab_activation(self) -> None:
        self.activation_widget = activation_widget = QWidget()
        activation_widget.setLayout(QVBoxLayout())
        activation_widget.layout().addWidget(
            QMessageBox(
                QMessageBox.Information,
                "About",
                "This is the activation tab",
            )
        )
        self.tab_widget.addTab(activation_widget, "Activation")

    def show(self) -> None:
        super().show()

    def closeEvent(self, event: QEvent) -> None:
        event.accept()
        self.hide()
