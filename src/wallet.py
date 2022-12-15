import random
from typing import List, Dict, Optional, Union

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QWidget
from mvclib import Unspent, Key
from mvclib.constants import Chain
from mvclib.hd import Xprv, derive_xkeys_from_xkey, Xpub
from mvclib.service import MetaSV
from mvclib.utils import decode_address

from base import copy_to_clipboard, set_table_view, UnspentModel, FtModel, copy_table_selected, table_select_all
from designer.wallet import Ui_formWallet
from keys import KeysUi
from metasv import ft_balance, TIMEOUT
from send_ft import SendFtUi
from send_unspents import SendUnspentsUi
from utils import format_coin


class RefreshUnspentThread(QtCore.QThread):
    refreshed = QtCore.pyqtSignal(object)

    def __init__(self, key: Union[Xprv, Xpub, Key, str], client_key: str):
        super(RefreshUnspentThread, self).__init__()
        self.kwargs = {'throw': True}
        if type(key) is Xprv:
            self.kwargs.update({'xprv': key})
            self.chain = key.chain
            self.xkey = True
        elif type(key) is Xpub:
            self.kwargs.update({'xpub': key})
            self.chain = key.chain
            self.xkey = True
        elif type(key) is Key:
            self.kwargs.update({'private_keys': [key]})
            self.chain = key.chain
            self.xkey = False
        else:
            self.kwargs.update({'address': key})
            _, self.chain = decode_address(key)
            self.xkey = False
        self.provider = None
        self.update_fields(client_key)

    def update_fields(self, client_key: str):
        self.provider = MetaSV(chain=self.chain, timeout=TIMEOUT, client_key=client_key)

    def run(self):
        try:
            unspents = self.provider.get_xpub_unspents(**self.kwargs) if self.xkey else self.provider.get_unspents(**self.kwargs)
            self.refreshed.emit([Unspent(**unspent) for unspent in unspents])
        except Exception as e:
            print(f'refresh unspent thread exception: {e}')
            self.refreshed.emit(None)


class RefreshFtThread(QtCore.QThread):
    refreshed = QtCore.pyqtSignal(object)

    def __init__(self, address: str, client_key: str):
        super(RefreshFtThread, self).__init__()
        self.address = address
        self.client_key = None
        self.update_fields(client_key)

    def update_fields(self, client_key: str):
        self.client_key = client_key or '-'

    def run(self):
        try:
            self.refreshed.emit(ft_balance(self.address, self.client_key, throw=True))
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

        self.xkey: Union[Xprv, Xpub, None] = None
        self.key: Optional[Key] = None
        self.address: str = ''
        if w.get('xprv'):
            self.xkey = Xprv(w['xprv'])
            self.key = derive_xkeys_from_xkey(self.xkey, 0, 1, 0)[0].private_key()
            self.address = self.key.address()
        elif w.get('xpub'):
            self.xkey = Xpub(w['xpub'])
            self.address = derive_xkeys_from_xkey(self.xkey, 0, 1, 0)[0].address()
        elif w.get('wif'):
            self.key = Key(w['wif'])
            self.address = self.key.address()
        else:
            self.address = w['address']
        _, self.chain = decode_address(self.address)

        if self.xkey:
            self.keys_widget = KeysUi(self.password, self.w)
            self.keys_widget.request_refresh.connect(self.refresh_button_clicked)
            unspent_address = derive_xkeys_from_xkey(self.xkey, self.w['receive_index'], self.w['receive_index'] + 1, 0)[0].address()
        else:
            self.keys_widget = None
            unspent_address = self.address

        self.labelUnspentBalance.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.labelUnspentSymbol.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.labelUnspentAddress.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.labelFtAddress.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)

        watch_only_hint = '（观察钱包）' if self.key is None else ''
        chain_hint = '（测试网）' if self.chain == Chain.TEST else '（主网）'
        self.labelHint.setText(chain_hint + watch_only_hint)
        self.labelUnspentAddress.setText(unspent_address)
        self.labelFtAddress.setText(self.address)
        self.toolBox.setCurrentIndex(0)

        self.refresh_unspent_thread = RefreshUnspentThread(self.xkey or self.key or self.address, self.app_settings['client_key'])
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

        self.refresh_ft_thread = RefreshFtThread(self.address, self.app_settings['client_key'])
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

        if self.key is None:
            self.pushButtonUnspentSend.setVisible(False)
            self.pushButtonFtSend.setVisible(False)
        if self.xkey is None:
            self.toolButtonUnspentAddressChange.setVisible(False)
            self.toolButtonUnspentKeys.setVisible(False)

    def unspent_address_change_button_clicked(self):
        self.w['receive_index'] = (self.w['receive_index'] + 1) % self.w['receive_limit']
        unspent_address = derive_xkeys_from_xkey(self.xkey, self.w['receive_index'], self.w['receive_index'] + 1, 0)[0].address()
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
        if self.keys_widget:
            self.keys_widget.close()
        super().closeEvent(a0)

    def refresh_unspent_table_and_balance(self, unspents: Optional[List[Unspent]]):
        if unspents is not None:
            self.unspent_model.update_fields(unspents)
            self.tableViewUnspent.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
            self.tableViewUnspent.clearSelection()
            self.labelUnspentBalance.setText(format_coin(sum([unspent.satoshi for unspent in unspents])))
            self.toolBox.setItemText(self.toolBox.indexOf(self.pageUnspent), f'UTXO（{len(unspents)}）' if unspents else 'UTXO')
            self.pushButtonUnspentSend.setEnabled(len(unspents) > 0)
        self.network_status_updated.emit(unspents is not None)
        if self.keys_widget:
            self.keys_widget.update_fields(unspents=unspents)

    def unspent_send_button_clicked(self):
        unspents_selected = self.unspents_selected()
        combine = True if len(unspents_selected) > 0 else False
        unspents = unspents_selected or self.unspent_model.unspents
        if self.xkey:
            change_index = random.randrange(0, self.w['change_limit'])
            change_address = derive_xkeys_from_xkey(self.xkey, change_index, change_index + 1, 1)[0].address()
        else:
            change_address = self.address
        dialog = SendUnspentsUi(self.password, unspents, self.chain, change_address, combine)
        if dialog.exec():
            self.tableViewUnspent.clearSelection()
            self.refresh_button_clicked()

    def unspents_selected(self) -> List[Unspent]:
        unspents: List[Unspent] = []
        for row in set(index.row() for index in self.tableViewUnspent.selectedIndexes()):
            unspents.append(self.unspent_model.unspents[row])
        return unspents

    def enable_ft_send_button(self):
        self.pushButtonFtSend.setEnabled(len(self.fts_selected()) == 1)

    def refresh_ft_table(self, fts: Optional[List[Dict]]):
        if fts is not None:
            self.ft_model.update_fields(fts)
            self.tableViewFt.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
            self.toolBox.setItemText(self.toolBox.indexOf(self.pageFt), f'Token（{self.ft_model.rowCount()}）' if self.ft_model.rowCount() else 'Token')
        self.network_status_updated.emit(fts is not None)

    def ft_send_button_clicked(self):
        dialog = SendFtUi(self.password, self.fts_selected()[0], self.key, self.unspent_model.unspents)
        if dialog.exec():
            self.tableViewFt.clearSelection()
            self.refresh_button_clicked()

    def fts_selected(self) -> List[Dict]:
        fts: List[Dict] = []
        for row in set(index.row() for index in self.tableViewFt.selectedIndexes()):
            fts.append(self.ft_model.fts[row])
        return fts

    def update_fields(self, app_settings: Optional[Dict] = None, password: Optional[str] = None, w: Optional[Dict] = None):
        if app_settings is not None:
            self.app_settings = app_settings
            self.refresh_unspent_thread.update_fields(self.app_settings['client_key'])
            self.refresh_ft_thread.update_fields(self.app_settings['client_key'])
            self.refresh_button_clicked()
        if password is not None:
            self.password = password
            if self.keys_widget:
                self.keys_widget.update_fields(password=self.password)
        if w is not None:
            self.w = w
            if self.keys_widget:
                self.keys_widget.update_fields(w=self.w)
