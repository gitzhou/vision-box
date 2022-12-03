from typing import Callable

from PyQt6 import QtCore
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from designer.input_dialog import Ui_dialogInput


def _not_blank(s: str) -> bool:
    return True if s else False


class InputDialogUi(QDialog, Ui_dialogInput):
    text_entered = QtCore.pyqtSignal(str)

    def __init__(self, validator: Callable[[str], bool] = _not_blank):
        super(InputDialogUi, self).__init__()
        self.setupUi(self)

        self.validator = validator

        self.setFixedSize(self.geometry().width(), self.geometry().height())
        self.minimum_width = self.geometry().width()
        self.labelDescription.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lineEdit.textChanged.connect(self.enable_ok_button)
        self.lineEdit.textChanged.connect(self.resize_to_content)
        self.lineEdit.setMaxLength(150)
        self.lineEdit.setFocus()
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.buttonBox.accepted.connect(self.emit_text)

    def enable_ok_button(self):
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(self.validator(self.lineEdit.text().strip()))

    def resize_to_content(self):
        fm = self.lineEdit.fontMetrics()
        width = max(fm.boundingRect(self.lineEdit.text().strip()).width() + 80, self.minimum_width)
        x = self.geometry().x() - (width - self.geometry().width()) // 2
        if x > 0:
            g = self.geometry()
            g.setX(x)
            self.setGeometry(g)
        self.setFixedSize(width, self.geometry().height())

    def emit_text(self):
        self.text_entered.emit(self.lineEdit.text().strip())
