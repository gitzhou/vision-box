import re
from contextlib import suppress
from enum import Enum

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QDialog
from mvclib.constants import Chain
from mvclib.hd import validate_mnemonic, Xprv, Xpub, derive_xprv_from_mnemonic

from designer.hd import Ui_dialogHdBackup


class Mode(str, Enum):
    HD = 'hd'
    Xprv = 'xprv'
    Xpub = 'xpub'
    Readonly = 'readonly'


class HdUi(QDialog, Ui_dialogHdBackup):
    mnemonic_path_passphrase_set = QtCore.pyqtSignal(object)

    def __init__(self, mnemonic: str = '', path: str = '', passphrase: str = '', xprv: str = '', xpub: str = '', chain: Chain = Chain.MAIN, mode: Mode = Mode.HD):
        super(HdUi, self).__init__()
        self.setupUi(self)

        self.chain: Chain = chain
        if xprv:
            self.chain = Xprv(xprv).chain
        elif xpub:
            self.chain = Xpub(xpub).chain

        self.setFixedSize(self.geometry().width(), self.geometry().height())
        self.lineEditPath.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression("[m/'0-9]*"), self))
        self.lineEditPassphrase.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression("[\x21-\x7E]*"), self))

        self.plainTextEditMnemonic.setPlainText(mnemonic)
        self.lineEditPath.setText(path)
        self.lineEditPassphrase.setText(passphrase)
        self.plainTextEditXprv.setPlainText(xprv)
        self.plainTextEditXpub.setPlainText(xpub)

        self.plainTextEditMnemonic.textChanged.connect(self.derive_from_mnemonic)
        self.lineEditPath.textChanged.connect(self.derive_from_mnemonic)
        self.lineEditPassphrase.textChanged.connect(self.derive_from_mnemonic)
        self.plainTextEditXprv.textChanged.connect(self.derive_from_xprv)
        self.pushButtonOk.setEnabled(False)
        self.plainTextEditXpub.textChanged.connect(self.enable_ok_button)
        self.pushButtonOk.clicked.connect(self.ok_button_clicked)

        if mode == Mode.HD:
            self.plainTextEditMnemonic.setReadOnly(False)
            self.lineEditPath.setReadOnly(False)
            self.lineEditPassphrase.setReadOnly(False)
            self.plainTextEditMnemonic.setFocus()
            self.derive_from_mnemonic()
        elif mode == Mode.Xprv:
            self.plainTextEditXprv.setReadOnly(False)
            self.plainTextEditXprv.setFocus()
            self.derive_from_xprv()
        elif mode == Mode.Xpub:
            self.plainTextEditXpub.setReadOnly(False)
            self.plainTextEditXpub.setFocus()
        else:
            if mnemonic:
                self.derive_from_mnemonic()
            if xprv:
                self.derive_from_xprv()

        self.enable_ok_button()

    def enable_ok_button(self):
        self.pushButtonOk.setEnabled(self.xpub_valid() or self.mnemonic_valid() and self.path_valid())

    def mnemonic_valid(self) -> bool:
        with suppress(Exception):
            validate_mnemonic(mnemonic=self.plainTextEditMnemonic.toPlainText().strip())
            return True
        return False

    def path_valid(self) -> bool:
        match_groups = re.match(r"^m(/\d+'?)+$", self.lineEditPath.text().strip())
        return True if match_groups else False

    def xprv_valid(self) -> bool:
        with suppress(Exception):
            xprv = Xprv(self.plainTextEditXprv.toPlainText().strip())
            assert xprv.chain == self.chain
            return True
        return False

    def xpub_valid(self) -> bool:
        with suppress(Exception):
            xpub = Xpub(self.plainTextEditXpub.toPlainText().strip())
            assert xpub.chain == self.chain
            return True
        return False

    def ok_button_clicked(self):
        self.mnemonic_path_passphrase_set.emit({
            'mnemonic': self.plainTextEditMnemonic.toPlainText().strip(),
            'path': self.lineEditPath.text(),
            'passphrase': self.lineEditPassphrase.text(),
            'xprv': self.plainTextEditXprv.toPlainText().strip(),
            'xpub': self.plainTextEditXpub.toPlainText().strip(),
        })

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() in [QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Escape]:
            return
        else:
            super().keyPressEvent(a0)

    def derive_from_mnemonic(self):
        text = ''
        if self.mnemonic_valid() and self.path_valid():
            mnemonic = self.plainTextEditMnemonic.toPlainText().strip()
            path = self.lineEditPath.text().strip()
            passphrase = self.lineEditPassphrase.text()
            text = str(derive_xprv_from_mnemonic(mnemonic=mnemonic, passphrase=passphrase, path=path, chain=self.chain))
        self.plainTextEditXprv.setPlainText(text)

    def derive_from_xprv(self):
        self.plainTextEditXpub.setPlainText(str(Xprv(self.plainTextEditXprv.toPlainText().strip()).xpub()) if self.xprv_valid() else '')
