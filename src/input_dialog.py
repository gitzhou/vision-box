from typing import Callable, Optional

from PyQt6 import QtCore
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from designer.input_dialog import Ui_dialogInput


def _not_blank(s: str) -> bool:
    return True if s else False


class InputDialogUi(QDialog, Ui_dialogInput):
    text_entered = QtCore.pyqtSignal(str)

    def __init__(self, validator: Optional[Callable[[str], bool]] = None):
        super(InputDialogUi, self).__init__()
        self.setupUi(self)

        self.validator = validator if validator else _not_blank
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.lineEdit.textChanged.connect(self.enable_ok_button)

        self.lineEdit.setFocus()
        self.setFixedSize(self.geometry().width(), self.geometry().height())

        self.buttonBox.accepted.connect(self.emit_text)

    def enable_ok_button(self):
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(self.validator(self.lineEdit.text()))

    def emit_text(self):
        self.text_entered.emit(self.lineEdit.text())
