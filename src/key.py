from PyQt6.QtWidgets import QDialog
from mvclib import Key, PublicKey
from mvclib.constants import Chain

from designer.key import Ui_dialogKey


class KeyUi(QDialog, Ui_dialogKey):

    def __init__(self, wif: str = '', pk: str = '', address: str = '', chain: Chain = Chain.MAIN):
        super(KeyUi, self).__init__()
        self.setupUi(self)

        self.setFixedSize(self.geometry().width(), self.geometry().height())

        key_hex = ''
        if wif:
            _k = Key(wif)
            key_hex = _k.hex()
            pk = _k.public_key().hex()
            address = _k.address()
        elif pk and not address:
            _pk = PublicKey(pk)
            address = _pk.address(chain=chain)

        self.lineEditWif.setText(wif)
        self.plainTextKeyHex.setPlainText(key_hex)
        self.plainTextEditPk.setPlainText(pk)
        self.lineEditAddress.setText(address)
