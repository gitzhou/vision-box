from typing import Callable, Optional

from PyQt6 import QtCore
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from designer.input_dialog import Ui_dialogInput


class InputDialogUi(QDialog, Ui_dialogInput):
    text_entered = QtCore.pyqtSignal(str)

    def __init__(self, validator: Optional[Callable[[str], bool]] = None):
        super(InputDialogUi, self).__init__()
        self.setupUi(self)

        if validator:
            self.validator = validator
            self.lineEdit.textChanged.connect(self.enable_ok_button)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(validator is None)

        self.lineEdit.setFocus()
        self.setFixedSize(self.geometry().width(), self.geometry().height())

        self.buttonBox.accepted.connect(self.emit_text)

    def enable_ok_button(self):
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(self.validator(self.lineEdit.text()))

    def emit_text(self):
        self.text_entered.emit(self.lineEdit.text())
