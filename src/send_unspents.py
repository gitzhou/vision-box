import re
from decimal import Decimal
from typing import List, Optional, Tuple

from PyQt6 import QtGui, QtCore
from PyQt6.QtWidgets import QDialog, QAbstractItemView, QMessageBox
from mvclib import Unspent, Transaction
from mvclib.constants import Chain, P2PKH_DUST_LIMIT
from mvclib.transaction import InsufficientFunds
from mvclib.utils import validate_address
from mvclib.wallet import create_transaction

from base import set_table_view, UnspentModel, require_password
from designer.send_unspents import Ui_dialogSendUnspents
from utils import COIN_DECIMAL, format_coin


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

        self.unspent_model = UnspentModel(self.unspents)
        self.tableViewUnspent.setModel(self.unspent_model)
        set_table_view(self.tableViewUnspent)
        self.tableViewUnspent.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.lineEditTotalInput.setText(format_coin(sum([unspent.satoshi for unspent in self.unspents])))
        self.lineEditAmount.setReadOnly(True)
        self.toolButtonMaxAmount.setEnabled(False)
        self.pushButtonSend.setEnabled(False)
        self.plainTextEditReceivers.textChanged.connect(self.receivers_text_changed)
        self.lineEditAmount.textChanged.connect(self.amount_text_changed)
        self.toolButtonMaxAmount.clicked.connect(self.max_amount_clicked)
        self.pushButtonSend.clicked.connect(lambda: require_password(self, self.send_transaction, self.password))

    def trim_blank_lines(self):
        lines = []
        for line in self.plainTextEditReceivers.toPlainText().splitlines():
            if line.strip():
                lines.append(line.strip())
        return lines

    regex_patter_receivers = r'^\s*(\S+)\s*[,，]\s*(\d+(\.\d{1,8})?)\s*$'
    regex_patter_amount = r'^\s*\d+(\.\d{1,8})?\s*$'

    def receivers_text_changed(self):
        lines = self.trim_blank_lines()
        self.lineEditAmount.setReadOnly(len(lines) != 1)
        self.toolButtonMaxAmount.setEnabled(len(lines) == 1)
        receivers_valid = self.receivers_valid()
        self.pushButtonSend.setEnabled(self.amount_valid() and receivers_valid)
        if len(lines) > 1:
            if receivers_valid:
                groups = re.findall(SendUnspentsUi.regex_patter_receivers, '\n'.join(lines), re.MULTILINE)
                total_amount = sum([Decimal(amount) for amount in [group[1] for group in groups]])
                self.lineEditAmount.setText(str(total_amount))
            else:
                self.lineEditAmount.setText('')

    def amount_text_changed(self):
        self.pushButtonSend.setEnabled(self.amount_valid() and self.receivers_valid())

    def receivers_valid(self) -> bool:
        lines = self.trim_blank_lines()
        if len(lines) == 0:
            valid = False
        elif len(lines) == 1:
            valid = validate_address(lines[0], self.chain)
        else:
            groups = re.findall(SendUnspentsUi.regex_patter_receivers, '\n'.join(lines), re.MULTILINE)
            valid = len(groups) == len(lines) and all([validate_address(address, self.chain) for address in [group[0] for group in groups]])
        return valid

    def amount_valid(self) -> bool:
        text = self.lineEditAmount.text()
        if not text:
            valid = False
        else:
            match_groups = re.match(SendUnspentsUi.regex_patter_amount, text)
            amount = Decimal(text) * 10 ** COIN_DECIMAL if match_groups else -1
            valid = amount >= P2PKH_DUST_LIMIT
        return valid

    def parse_receivers(self):
        lines = self.trim_blank_lines()
        if len(lines) == 1:
            self.receivers = [(lines[0], int(Decimal(self.lineEditAmount.text()) * 10 ** COIN_DECIMAL))]
        else:
            self.receivers = []
            groups = re.findall(SendUnspentsUi.regex_patter_receivers, '\n'.join(lines), re.MULTILINE)
            for group in groups:
                self.receivers.append((group[0], int(Decimal(group[1]) * 10 ** COIN_DECIMAL)))

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
