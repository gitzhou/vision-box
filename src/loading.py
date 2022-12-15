from typing import Optional

from PyQt6 import QtGui, QtCore
from PyQt6.QtWidgets import QDialog, QLabel, QGridLayout


class LoadingUi(QDialog):

    def __init__(self, text: Optional[str] = None):
        super(LoadingUi, self).__init__()
        self.setFixedSize(400, 100)
        label = QLabel(text or '')
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setLayout(QGridLayout())
        self.layout().addWidget(label)
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() in [QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Escape]:
            return
        else:
            super().keyPressEvent(a0)
