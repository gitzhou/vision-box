import re
from decimal import Decimal
from typing import List, Dict, Optional

from PyQt6 import QtGui, QtCore
from PyQt6.QtWidgets import QDialog, QMessageBox
from mvclib import Key, Unspent, Transaction
from mvclib.utils import validate_address

from base import require_password
from contract import Contract
from designer.send_ft import Ui_dialogSendFt
from loading import LoadingUi
from utils import format_coin, splitlines_without_blank


class SendFtUi(QDialog, Ui_dialogSendFt):
    def __init__(self, password: str, ft: Dict, key: Key, unspents: Optional[List[Unspent]] = None):
        super(SendFtUi, self).__init__()
        self.setupUi(self)

        self.contract = Contract()
        self.password = password
        self.ft = ft
        self.key = key
        self.unspents = unspents or []
        self.receivers: List[Dict] = []
        self.regex_patter_receivers = f'^\\s*(\\S+)\\s*[,，]\\s*(\\d+(\\.\\d{{1,{self.ft["decimal"]}}})?)\\s*$'
        self.regex_patter_amount = f'^\\s*\\d+(\\.\\d{{1,{self.ft["decimal"]}}})?\\s*$'
        self.loading = LoadingUi(f'Sending {self.ft["name"]} ({self.ft["symbol"]}) ...')

        self.setWindowTitle(f'Send / {self.ft["name"]} ({self.ft["symbol"]})')
        self.labelFtSymbol.setText(self.ft['symbol'])
        self.lineEditAmount.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(self.regex_patter_amount), self))

        self.lineEditAmount.setReadOnly(True)
        self.toolButtonMaxAmount.setEnabled(False)
        self.pushButtonSend.setEnabled(False)
        self.plainTextEditReceivers.textChanged.connect(self.receivers_text_changed)
        self.lineEditAmount.textChanged.connect(self.amount_text_changed)
        self.toolButtonMaxAmount.clicked.connect(self.max_amount_clicked)
        self.pushButtonSend.clicked.connect(lambda: require_password(self, self.send_ft, self.password))

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
        if len(lines) == 0 or len(lines) > 99:
            valid = False
        else:
            groups = re.findall(self.regex_patter_receivers, '\n'.join(lines), re.MULTILINE)
            address_all_valid = all([validate_address(address, self.key.chain) for address in [group[0] for group in groups]])
            amount_all_valid = all([int(Decimal(amount) * 10 ** self.ft['decimal']) > 0 for amount in [group[1] for group in groups]])
            valid = len(groups) == len(lines) and address_all_valid and amount_all_valid
        if not valid and len(lines) == 1:
            valid = validate_address(lines[0], self.key.chain)
        return valid

    def amount_valid(self) -> bool:
        text = self.lineEditAmount.text()
        return Decimal(text) * 10 ** self.ft['decimal'] > 0 if text else False

    def parse_receivers(self):
        lines = splitlines_without_blank(self.plainTextEditReceivers.toPlainText())
        self.receivers = []
        groups = re.findall(self.regex_patter_receivers, '\n'.join(lines), re.MULTILINE)
        for group in groups:
            self.receivers.append({'address': group[0], 'amount': str(int(Decimal(group[1]) * 10 ** self.ft['decimal']))})
        if not self.receivers and len(lines) == 1:
            self.receivers = [{'address': lines[0], 'amount': str(int(Decimal(self.lineEditAmount.text()) * 10 ** self.ft['decimal']))}]

    def send_ft(self):
        self.parse_receivers()
        try:
            # 合并 Gas
            if not self.unspents:
                QMessageBox.information(self, 'Information', f'Cannot send {self.ft["symbol"]} without SPACE available.', QMessageBox.StandardButton.Ok)
                return
            if len([self.key.address() == unspent.address for unspent in self.unspents]) > 3:
                Transaction(chain=self.key.chain).add_inputs(self.unspents).add_change(self.key.address()).sign().broadcast()
            # 发送 FT
            self.contract.ft_transfer(self.ft, self.key, self.receivers, self.send_ft_callback)
            self.loading.exec()
        except Exception as e:
            QMessageBox.critical(self, 'Critical', f'Unknown exception.\n\n{e}', QMessageBox.StandardButton.Ok)

    def send_ft_callback(self, r: Dict):
        self.loading.accept()
        if r['code'] == 0:
            QMessageBox.information(self, 'Information', f'Sent successfully.\n\n{r["txid"]}', QMessageBox.StandardButton.Ok)
            self.accept()
        else:
            message = r['message']
            if r['code'] == -200:
                message = 'Insufficient SPACE'
            elif r['code'] == -201:
                message = f'Insufficient {self.ft["symbol"]}'
            QMessageBox.critical(self, 'Critical', f'Failed to send.\n\n{message}', QMessageBox.StandardButton.Ok)

    def max_amount_clicked(self):
        self.lineEditAmount.setText(format_coin(int(self.ft['confirmedString']) + int(self.ft['unconfirmedString']), self.ft['decimal']))

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() in [QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Escape]:
            return
        else:
            super().keyPressEvent(a0)
