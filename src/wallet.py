import random
from typing import List, Dict, Optional

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QWidget
from mvclib import WalletLite, Unspent, Key
from mvclib.constants import Chain
from mvclib.hd import Xprv, derive_xkeys_from_xkey

from base import copy_to_clipboard, set_table_view, still_under_development, UnspentModel, FtModel, copy_table_selected, table_select_all
from designer.wallet import Ui_formWallet
from keys import KeysUi
from metasv import ft_balance
from send_unspents import SendUnspentsUi
from utils import format_coin


class RefreshUnspentThread(QtCore.QThread):
    refreshed = QtCore.pyqtSignal(object)

    def __init__(self, w: WalletLite):
        super(RefreshUnspentThread, self).__init__()
        self.w = w

    def run(self):
        try:
            self.refreshed.emit(self.w.get_unspents(refresh=True, throw=True))
        except Exception as e:
            print(f'refresh unspent thread exception: {e}')
            self.refreshed.emit(None)


class RefreshFtThread(QtCore.QThread):
    refreshed = QtCore.pyqtSignal(object)

    def __init__(self, k: Key, client_key: str = ''):
        super(RefreshFtThread, self).__init__()
        self.address = k.address()
        self.chain = k.chain
        self.client_key = client_key

    def run(self):
        try:
            self.refreshed.emit(ft_balance(self.address, self.chain, self.client_key, throw=True))
        except Exception as e:
            print(f'refresh ft thread exception: {e}')
            self.refreshed.emit(None)


class WalletUi(QWidget, Ui_formWallet):
    wallet_updated = QtCore.pyqtSignal(object, int)
    network_status_updated = QtCore.pyqtSignal(bool)

    def __init__(self, app_settings: Dict, password: str, w: Dict, account_index: int):
        super(WalletUi, self).__init__()
        self.setupUi(self)

        self.app_settings = app_settings
        self.password = password
        self.w: Dict = w
        self.account_index: int = account_index
        self.xprv = Xprv(self.w['xprv'])
        self.k: Key = derive_xkeys_from_xkey(self.xprv, 0, 1, 0)[0].private_key()
        self.chain: Chain = self.xprv.chain
        self.keys_widget = KeysUi(self.password, self.w)
        self.keys_widget.request_refresh.connect(self.refresh_button_clicked)
        self.send_unspents_dialog = None

        self.labelUnspentBalance.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.labelUnspentSymbol.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.labelUnspentAddress.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.labelFtAddress.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)

        self.labelChain.setText('（测试网）' if self.chain == Chain.TEST else '（主网）')
        unspent_address = derive_xkeys_from_xkey(self.xprv, self.w['receive_index'], self.w['receive_index'] + 1, 0)[0].address()
        self.labelUnspentAddress.setText(unspent_address)
        self.labelFtAddress.setText(self.k.address())
        self.toolBox.setCurrentIndex(0)

        self.refresh_unspent_thread = RefreshUnspentThread(WalletLite(self.xprv, client_key=self.app_settings['client_key'] or '-'))
        self.refresh_unspent_thread.refreshed.connect(self.refresh_unspent_table_and_balance)
        self.unspent_model = UnspentModel()
        self.tableViewUnspent.setModel(self.unspent_model)
        set_table_view(self.tableViewUnspent)
        self.toolButtonUnspentAddressCopy.clicked.connect(lambda: copy_to_clipboard(self.labelUnspentAddress.text()))
        self.toolButtonUnspentAddressChange.clicked.connect(self.unspent_address_change_button_clicked)
        self.toolButtonUnspentKeys.clicked.connect(self.keys_button_clicked)
        self.pushButtonUnspentSend.setEnabled(False)
        self.pushButtonUnspentSend.clicked.connect(self.unspent_send_button_clicked)
        self.pushButtonUnspentClearSelection.clicked.connect(self.tableViewUnspent.clearSelection)
        self.pushButtonUnspentCopy.clicked.connect(lambda: copy_table_selected(self.tableViewUnspent))
        self.pushButtonUnspentSelectAll.clicked.connect(lambda: table_select_all(self.tableViewUnspent))

        self.refresh_ft_thread = RefreshFtThread(self.k, self.app_settings['client_key'])
        self.refresh_ft_thread.refreshed.connect(self.refresh_ft_table)
        self.ft_model = FtModel()
        self.tableViewFt.setModel(self.ft_model)
        set_table_view(self.tableViewFt)
        self.toolButtonFtAddressCopy.clicked.connect(lambda: copy_to_clipboard(self.labelFtAddress.text()))
        self.pushButtonFtSend.setEnabled(False)
        self.pushButtonFtSend.clicked.connect(self.ft_send_button_clicked)
        self.pushButtonFtClearSelection.clicked.connect(self.tableViewFt.clearSelection)
        self.tableViewFt.selectionModel().selectionChanged.connect(self.enable_ft_send_button)
        self.pushButtonFtCopy.clicked.connect(lambda: copy_table_selected(self.tableViewFt))
        self.pushButtonFtSelectAll.clicked.connect(lambda: table_select_all(self.tableViewFt))

        self.refresh_button_enable_timer = QtCore.QTimer(self)
        # noinspection PyUnresolvedReferences
        self.refresh_button_enable_timer.timeout.connect(lambda: self.pushButtonRefresh.setEnabled(True))

        self.pushButtonRefresh.clicked.connect(self.refresh_button_clicked)
        self.refresh_button_clicked()

    def unspent_address_change_button_clicked(self):
        self.w['receive_index'] = (self.w['receive_index'] + 1) % self.w['receive_limit']
        unspent_address = derive_xkeys_from_xkey(self.xprv, self.w['receive_index'], self.w['receive_index'] + 1, 0)[0].address()
        self.labelUnspentAddress.setText(unspent_address)
        self.wallet_updated.emit(self.w, self.account_index)

    def keys_button_clicked(self):
        if self.keys_widget.isVisible():
            self.keys_widget.hide()
        else:
            self.keys_widget.show()

    def refresh_button_clicked(self):
        self.pushButtonRefresh.setEnabled(False)
        self.refresh_button_enable_timer.start(10 * 1000)
        if not self.refresh_unspent_thread.isRunning():
            self.refresh_unspent_thread.start()
        if not self.refresh_ft_thread.isRunning():
            self.refresh_ft_thread.start()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.keys_widget.close()
        super().closeEvent(a0)

    def refresh_unspent_table_and_balance(self, unspents: Optional[List[Unspent]]):
        if unspents is not None:
            self.unspent_model.refresh(unspents)
            self.tableViewUnspent.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
            self.labelUnspentBalance.setText(format_coin(sum([unspent.satoshi for unspent in unspents])))
            self.toolBox.setItemText(self.toolBox.indexOf(self.pageUnspent), f'UTXO（{len(unspents)}）' if unspents else 'UTXO')
            self.pushButtonUnspentSend.setEnabled(len(unspents) > 0)
            self.keys_widget.refresh(unspents)
        self.network_status_updated.emit(unspents is not None)

    def unspent_send_button_clicked(self):
        unspents_selected = self.unspents_selected()
        combine = True if len(unspents_selected) > 0 else False
        unspents = unspents_selected or self.unspent_model.unspents
        change_index = random.randrange(0, self.w['change_limit'])
        change_address = derive_xkeys_from_xkey(self.xprv, change_index, change_index + 1, 1)[0].address()
        self.send_unspents_dialog = SendUnspentsUi(self.password, unspents, self.chain, change_address, combine)
        if self.send_unspents_dialog.exec():
            self.tableViewUnspent.clearSelection()
            self.refresh_button_clicked()

    def unspents_selected(self) -> List[Unspent]:
        unspents: List[Unspent] = []
        for row in list(set(index.row() for index in self.tableViewUnspent.selectedIndexes())):
            unspents.append(self.unspent_model.unspents[row])
        return unspents

    def enable_ft_send_button(self):
        self.pushButtonFtSend.setEnabled(len(self.fts_selected()) > 0)

    def refresh_ft_table(self, fts: Optional[List[Dict]]):
        if fts is not None:
            self.ft_model.refresh(fts)
            self.tableViewFt.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
            self.toolBox.setItemText(self.toolBox.indexOf(self.pageFt), f'Token（{len(fts)}）' if fts else 'Token')
        self.network_status_updated.emit(fts is not None)

    def ft_send_button_clicked(self):
        fts_selected = self.fts_selected()
        for ft in fts_selected:
            print(ft)
        still_under_development(self)

    def fts_selected(self) -> List[Dict]:
        fts: List[Dict] = []
        for row in list(set(index.row() for index in self.tableViewFt.selectedIndexes())):
            fts.append(self.ft_model.fts[row])
        return fts
