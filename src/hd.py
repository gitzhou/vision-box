import re
from contextlib import suppress

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QDialog
from mvclib.constants import BIP44_DERIVATION_PATH
from mvclib.hd import validate_mnemonic

from designer.hd import Ui_dialogHdBackup


class HdUi(QDialog, Ui_dialogHdBackup):
    mnemonic_path_passphrase_set = QtCore.pyqtSignal(object)

    def __init__(self, mnemonic: str = '', path: str = BIP44_DERIVATION_PATH, passphrase: str = '', readonly: bool = False):
        super(HdUi, self).__init__()
        self.setupUi(self)

        self.plainTextEditMnemonic.setFocus()
        self.setFixedSize(self.geometry().width(), self.geometry().height())
        self.plainTextEditMnemonic.setPlainText(mnemonic)
        self.lineEditPath.setText(path)
        self.lineEditPassphrase.setText(passphrase)
        self.plainTextEditMnemonic.setReadOnly(readonly)
        self.lineEditPath.setReadOnly(readonly)
        self.lineEditPassphrase.setReadOnly(readonly)
        self.pushButtonOk.setEnabled(False)

        self.plainTextEditMnemonic.textChanged.connect(self.enable_ok_button)
        self.lineEditPath.textChanged.connect(self.enable_ok_button)
        self.pushButtonOk.clicked.connect(self.ok_button_clicked)

        self.enable_ok_button()

    def enable_ok_button(self):
        self.pushButtonOk.setEnabled(self.mnemonic_valid() and self.path_valid())

    def mnemonic_valid(self) -> bool:
        with suppress(Exception):
            validate_mnemonic(mnemonic=self.plainTextEditMnemonic.toPlainText().strip())
            return True
        return False

    def path_valid(self) -> bool:
        match_groups = re.match(r"^m(/\d+'?)+$", self.lineEditPath.text().strip())
        return True if match_groups else False

    def ok_button_clicked(self):
        self.mnemonic_path_passphrase_set.emit({
            'mnemonic': self.plainTextEditMnemonic.toPlainText().strip(),
            'path': self.lineEditPath.text(),
            'passphrase': self.lineEditPassphrase.text()
        })

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() in [QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Escape]:
            return
        else:
            super().keyPressEvent(a0)
