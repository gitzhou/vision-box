from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QInputDialog, QStackedLayout, QLabel, QMenu
from mvclib import PublicKey
from mvclib.constants import BIP44_DERIVATION_PATH
from mvclib.hd import mnemonic_from_entropy, Xprv

from base import require_password, select_chain, font, activate, set_password
from designer.account import Ui_mainWindowAccount
from hd import HdUi, Mode
from input_dialog import InputDialogUi
from key import KeyUi
from utils import write_account_file, xprv_valid, xpub_valid, wif_valid, address_valid, pk_valid
from wallet import WalletUi


class WalletModel(QtCore.QAbstractListModel):

    def __init__(self, wallets: Optional[List[Dict]] = None):
        super(WalletModel, self).__init__()
        self.wallets: List[Dict] = []
        self._wallets: List[str] = []
        self.update_fields(wallets)

    def update_fields(self, wallets: Optional[List[Dict]] = None):
        self.wallets = wallets or []
        self._wallets = [f'  {wallet["name"]}' for wallet in self.wallets]

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._wallets[index.row()]
        elif role == QtCore.Qt.ItemDataRole.SizeHintRole:
            return QtCore.QSize(100, 45)
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            return font('Helvetica', 13)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._wallets)


class AccountUi(QMainWindow, Ui_mainWindowAccount):
    app_settings_updated = QtCore.pyqtSignal(object)

    def __init__(self, app_settings: Dict, account: List[Dict], account_file: str, password: str):
        super(AccountUi, self).__init__()
        self.setupUi(self)

        self.app_settings = app_settings
        self.account = account
        self.account_file = account_file
        self.password = password

        self.setWindowTitle(f'Account / {Path(self.account_file).stem}')
        self.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
        self.stacked_layout = QStackedLayout()
        self.widget.setLayout(self.stacked_layout)

        self.actionActivate.triggered.connect(lambda: activate(self.update_client_key))
        self.actionChangePassword.triggered.connect(lambda: require_password(self, set_password, self.password, slot=self.change_password))
        self.pushButtonNew.clicked.connect(lambda: require_password(self, self.new_wallet_clicked, self.password))
        self.pushButtonImport.clicked.connect(lambda: require_password(self, self.import_wallet_clicked, self.password))

        network = QLabel()
        network.setText('Network : ')
        self.statusbar.addWidget(network)
        self.network_status = QLabel()
        self.statusbar.addWidget(self.network_status)

        for i in range(len(self.account)):
            self.add_wallet_widget(self.account[i], i)

        self.model = WalletModel(self.account)
        self.listViewWallets.setModel(self.model)
        self.listViewWallets.selectionModel().selectionChanged.connect(self.wallet_list_selection_changed)
        self.listViewWallets.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.listViewWallets.customContextMenuRequested.connect(self.wallet_list_context_menu)
        self.select_wallet_in_list(0)

    def update_client_key(self, client_key: str):
        self.app_settings['client_key'] = client_key
        self.app_settings_updated.emit(self.app_settings)
        for i in range(self.stacked_layout.count()):
            w: WalletUi = self.stacked_layout.widget(i)
            w.update_fields(app_settings=self.app_settings)

    def change_password(self, password: str):
        self.password = password
        write_account_file(self.account, self.account_file, self.password)
        for i in range(self.stacked_layout.count()):
            w: WalletUi = self.stacked_layout.widget(i)
            w.update_fields(password=self.password)
        QMessageBox.information(self, 'Information', 'The password was changed successfully.', QMessageBox.StandardButton.Ok)

    def wallet_list_selection_changed(self, selected: QtCore.QItemSelection, last_selected: QtCore.QItemSelection):
        row = selected.indexes()[0].row() if selected.indexes() else last_selected.indexes()[0].row()
        self.select_wallet_in_list(row)

    def select_wallet_in_list(self, index: int):
        """Select an item in the wallet list"""
        if self.model.rowCount():
            index %= self.model.rowCount()
            # Update list selection
            self.listViewWallets.setCurrentIndex(self.model.index(index))
            # Display the corresponding widget
            self.stacked_layout.setCurrentIndex(index)

    def new_wallet_clicked(self):
        chain = select_chain(self)
        if chain:
            dialog = HdUi(mnemonic=mnemonic_from_entropy(), path=BIP44_DERIVATION_PATH, chain=chain, mode=Mode.Readonly)
            dialog.setWindowTitle('IMMEDIATELY ! BACK UP your "mnemonic", "path" and "passphrase" !')
            dialog.mnemonic_set.connect(self.add_hd)
            dialog.exec()

    def import_wallet_clicked(self):
        _hd, _others = 'Mnemonic', 'Others (Xprv / Private Key (WIF) / Xpub / Public Key / Address)'
        selected, ok = QInputDialog.getItem(self, 'Import Wallet', 'Select the way to import the wallet.', [_hd, _others], 0, False)
        if ok:
            if selected == _hd:
                chain = select_chain(self)
                if chain:
                    dialog = HdUi(chain=chain, mode=Mode.Mnemonic)
                    dialog.setWindowTitle('Import Wallet by Mnemonic')
                    dialog.mnemonic_set.connect(self.add_hd)
                    dialog.exec()
            elif selected == _others:
                dialog = InputDialogUi(validator=AccountUi.import_wallet_text_valid)
                dialog.setWindowTitle('Import')
                dialog.labelDescription.setText(f'Import the wallet in other ways.')
                dialog.text_entered.connect(self.import_wallet)
                dialog.exec()

    @classmethod
    def import_wallet_text_valid(cls, text) -> bool:
        return xprv_valid(text) or xpub_valid(text) or wif_valid(text) or address_valid(text) or pk_valid(text)

    def import_wallet(self, text: str):
        if text.startswith(('xprv', 'tprv')):
            self.add_hd({'xprv': text})
        elif text.startswith(('xpub', 'tpub')):
            self.add_hd({'xpub': text})
        elif text.startswith(('L', 'K', '5', 'c', '9')):
            self.add_key({'wif': text})
        elif text.startswith(('02', '03', '04')):
            chain = select_chain(self)
            if chain:
                self.add_key({'pk': text, 'address': PublicKey(text).address(chain=chain)})
        else:
            self.add_key({'address': text})

    def add_hd(self, hd: Dict):
        hd.update({'name': f'HD Wallet {len(self.account) + 1}', 'receive_index': 0, 'receive_limit': 150, 'change_limit': 50, })
        self.add_wallet(hd)

    def add_key(self, key: Dict):
        key.update({'name': f'Wallet {len(self.account) + 1}'})
        self.add_wallet(key)

    def add_wallet(self, wallet: Dict):
        self.account.append(wallet)
        write_account_file(self.account, self.account_file, self.password)
        self.refresh_wallet_list()
        self.add_wallet_widget(wallet, len(self.account) - 1)
        self.select_wallet_in_list(-1)

    def refresh_wallet_list(self):
        """Refresh the wallet list on the left side"""
        self.model.update_fields(self.account)
        # noinspection PyUnresolvedReferences
        self.model.layoutChanged.emit()

    def add_wallet_widget(self, wallet: Dict, account_index: int):
        """Add a wallet widget on the right side"""
        w = WalletUi(self.app_settings, self.password, wallet, account_index)
        w.wallet_updated.connect(self.wallet_updated)
        w.network_status_updated.connect(self.network_status_updated)
        self.stacked_layout.addWidget(w)

    def wallet_updated(self, wallet: Dict, account_index: int):
        self.account[account_index] = wallet
        write_account_file(self.account, self.account_file, self.password)

    def network_status_updated(self, connectivity: bool):
        texts = {True: 'All Good', False: 'Broke Down'}
        colors = {True: 'color: green', False: 'color: red'}
        self.network_status.setText(texts[connectivity])
        self.network_status.setStyleSheet(colors[connectivity])

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        for i in range(self.stacked_layout.count()):
            self.stacked_layout.widget(i).close()
        super().closeEvent(a0)

    def wallet_list_context_menu(self, pos):
        menu = QMenu()
        action_rename = menu.addAction('Rename')
        action_information = menu.addAction('Information')
        action = menu.exec(self.listViewWallets.mapToGlobal(pos))
        if action == action_rename:
            self.context_menu_action_rename_clicked()
        elif action == action_information:
            require_password(self, self.context_menu_action_information_clicked, self.password)

    def context_menu_action_rename_clicked(self):
        dialog = InputDialogUi()
        dialog.setWindowTitle('Rename')
        dialog.labelDescription.setText('Enter a new wallet name.')
        dialog.lineEdit.setText(self.account[self.listViewWallets.selectedIndexes()[0].row()]['name'])
        dialog.text_entered.connect(self.rename_wallet)
        dialog.exec()

    def rename_wallet(self, name: str):
        index = self.listViewWallets.selectedIndexes()[0].row()
        self.account[index]['name'] = name
        write_account_file(self.account, self.account_file, self.password)
        self.refresh_wallet_list()
        wallet_widget: WalletUi = self.stacked_layout.widget(index)
        wallet_widget.update_fields(w=self.account[index])

    def context_menu_action_information_clicked(self):
        w: Dict = self.account[self.listViewWallets.selectedIndexes()[0].row()]
        if w.get('mnemonic'):
            chain = Xprv(w['xprv']).chain
            dialog = HdUi(mnemonic=w['mnemonic'], path=w['path'], passphrase=w['passphrase'], chain=chain)
        elif w.get('xprv'):
            dialog = HdUi(xprv=w['xprv'])
        elif w.get('xpub'):
            dialog = HdUi(xpub=w['xpub'])
        elif w.get('wif'):
            dialog = KeyUi(wif=w['wif'])
        elif w.get('pk'):
            dialog = KeyUi(pk=w['pk'], address=w['address'])
        else:
            dialog = KeyUi(address=w['address'])
        dialog.setWindowTitle(f'Wallet / {w["name"]}')
        dialog.exec()
