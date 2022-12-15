import re
from decimal import Decimal
from typing import List, Optional, Tuple

from PyQt6 import QtGui, QtCore
from PyQt6.QtWidgets import QDialog, QAbstractItemView, QMessageBox
from mvclib import Unspent, Transaction
from mvclib.constants import Chain
from mvclib.transaction import InsufficientFunds
from mvclib.utils import validate_address
from mvclib.wallet import create_transaction

from base import set_table_view, UnspentModel, require_password
from designer.send_unspents import Ui_dialogSendUnspents
from utils import COIN_DECIMAL, format_coin, splitlines_without_blank


class SendUnspentsUi(QDialog, Ui_dialogSendUnspents):
    def __init__(self, password: str, unspents: List[Unspent], chain: Chain, change_address: Optional[str] = None, combine: bool = True):
        super(SendUnspentsUi, self).__init__()
        self.setupUi(self)

        self.password = password
        self.unspents: List[Unspent] = unspents or []
        self.chain: Chain = chain
        self.change_address = change_address
        self.combine = combine
        self.receivers: List[Tuple[str, int]] = []
        self.regex_patter_receivers = f'^\\s*(\\S+)\\s*[,，]\\s*(\\d+(\\.\\d{{1,{COIN_DECIMAL}}})?)\\s*$'
        self.regex_patter_amount = f'^\\s*\\d+(\\.\\d{{1,{COIN_DECIMAL}}})?\\s*$'

        self.lineEditTotalInput.setText(format_coin(sum([unspent.satoshi for unspent in self.unspents])))
        self.lineEditAmount.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(self.regex_patter_amount), self))

        self.unspent_model = UnspentModel(self.unspents)
        self.tableViewUnspent.setModel(self.unspent_model)
        set_table_view(self.tableViewUnspent)
        self.tableViewUnspent.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.lineEditAmount.setReadOnly(True)
        self.toolButtonMaxAmount.setEnabled(False)
        self.pushButtonSend.setEnabled(False)
        self.plainTextEditReceivers.textChanged.connect(self.receivers_text_changed)
        self.lineEditAmount.textChanged.connect(self.amount_text_changed)
        self.toolButtonMaxAmount.clicked.connect(self.max_amount_clicked)
        self.pushButtonSend.clicked.connect(lambda: require_password(self, self.send_transaction, self.password))

    # noinspection DuplicatedCode
    def receivers_text_changed(self):
        lines = splitlines_without_blank(self.plainTextEditReceivers.toPlainText())
        receivers_valid = self.receivers_valid()
        self.pushButtonSend.setEnabled(self.amount_valid() and receivers_valid)
        total_amount = ''
        if receivers_valid:
            groups = re.findall(self.regex_patter_receivers, '\n'.join(lines), re.MULTILINE)
            _total_amount = sum([Decimal(amount) for amount in [group[1] for group in groups]])
            if _total_amount:
                total_amount = str(_total_amount)
        self.lineEditAmount.setText(total_amount)
        self.lineEditAmount.setReadOnly(len(lines) > 1 or total_amount != '')
        self.toolButtonMaxAmount.setEnabled(len(lines) == 1 and total_amount == '')

    def amount_text_changed(self):
        self.pushButtonSend.setEnabled(self.amount_valid() and self.receivers_valid())

    def receivers_valid(self) -> bool:
        lines = splitlines_without_blank(self.plainTextEditReceivers.toPlainText())
        if len(lines) == 0:
            valid = False
        else:
            groups = re.findall(self.regex_patter_receivers, '\n'.join(lines), re.MULTILINE)
            address_all_valid = all([validate_address(address, self.chain) for address in [group[0] for group in groups]])
            amount_all_valid = all([int(Decimal(amount) * 10 ** COIN_DECIMAL) > 0 for amount in [group[1] for group in groups]])
            valid = len(groups) == len(lines) and address_all_valid and amount_all_valid
        if not valid and len(lines) == 1:
            valid = validate_address(lines[0], self.chain)
        return valid

    def amount_valid(self) -> bool:
        text = self.lineEditAmount.text()
        return Decimal(text) * 10 ** COIN_DECIMAL if text else False

    def parse_receivers(self):
        lines = splitlines_without_blank(self.plainTextEditReceivers.toPlainText())
        self.receivers = []
        groups = re.findall(self.regex_patter_receivers, '\n'.join(lines), re.MULTILINE)
        for group in groups:
            self.receivers.append((group[0], int(Decimal(group[1]) * 10 ** COIN_DECIMAL)))
        if not self.receivers and len(lines) == 1:
            self.receivers = [(lines[0], int(Decimal(self.lineEditAmount.text()) * 10 ** COIN_DECIMAL))]

    def send_transaction(self):
        self.parse_receivers()
        try:
            t = create_transaction(unspents=self.unspents, outputs=self.receivers, leftover=self.change_address, combine=self.combine, chain=self.chain)
            r = t.broadcast()
            if r.propagated:
                QMessageBox.information(self, '信息', f'发送成功。\n\n{r.data}', QMessageBox.StandardButton.Ok)
                self.accept()
            else:
                QMessageBox.critical(self, '错误', f'发送失败。\n\n{r.data}\n\n{t.hex()}', QMessageBox.StandardButton.Ok)
        except InsufficientFunds as e:
            _groups = re.findall(r'require (\d+) satoshi but only (\d+)', str(e))
            _message = f'输入数量不足。\n\n共需要 {format_coin(_groups[0][0])} SPACE，\n但只有 {format_coin(_groups[0][1])} SPACE。'
            QMessageBox.critical(self, '错误', _message, QMessageBox.StandardButton.Ok)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'未知错误。\n\n{e}', QMessageBox.StandardButton.Ok)

    def max_amount_clicked(self):
        t = Transaction(chain=self.chain).add_inputs(self.unspents).add_change()
        self.lineEditAmount.setText(format_coin(t.tx_outputs[0].satoshi))

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() in [QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Escape]:
            return
        else:
            super().keyPressEvent(a0)
