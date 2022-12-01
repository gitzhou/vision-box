from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QInputDialog, QStackedLayout, QLabel, QMenu
from mvclib.constants import BIP44_DERIVATION_PATH
from mvclib.hd import mnemonic_from_entropy

from base import require_password, select_chain, font, activate, set_password
from designer.account import Ui_mainWindowAccount
from hd import HdUi, Mode
from input_dialog import InputDialogUi
from utils import write_account_file, xprv_valid
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

        self.setWindowTitle(f'账户：{Path(self.account_file).stem}')
        self.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
        self.stacked_layout = QStackedLayout()
        self.widget.setLayout(self.stacked_layout)

        self.actionActivate.triggered.connect(lambda: activate(self.update_client_key))
        self.actionChangePassword.triggered.connect(lambda: require_password(self, self.action_change_password_clicked, self.password))
        self.pushButtonNew.clicked.connect(lambda: require_password(self, self.new_wallet_clicked, self.password))
        self.pushButtonImport.clicked.connect(lambda: require_password(self, self.import_wallet_clicked, self.password))

        network = QLabel()
        network.setText('网络连接：')
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
        # 默认选中第一个钱包
        self.select_wallet_in_list(0)

    def network_status_updated(self, connectivity: bool):
        texts = {True: '没问题', False: '拉胯了'}
        colors = {True: 'color: green', False: 'color: red'}
        self.network_status.setText(texts[connectivity])
        self.network_status.setStyleSheet(colors[connectivity])

    def update_client_key(self, client_key: str):
        self.app_settings['client_key'] = client_key
        self.app_settings_updated.emit(self.app_settings)
        for i in range(self.stacked_layout.count()):
            w: WalletUi = self.stacked_layout.widget(i)
            w.update_fields(app_settings=self.app_settings)

    def action_change_password_clicked(self):
        set_password(self.change_password)

    def change_password(self, password: str):
        self.password = password
        write_account_file(self.account, self.account_file, self.password)
        for i in range(self.stacked_layout.count()):
            w: WalletUi = self.stacked_layout.widget(i)
            w.update_fields(password=self.password)
        QMessageBox.information(self, '信息', '密码修改成功。', QMessageBox.StandardButton.Ok)

    def wallet_list_selection_changed(self, selected: QtCore.QItemSelection, last_selected: QtCore.QItemSelection):
        row = selected.indexes()[0].row() if selected.indexes() else last_selected.indexes()[0].row()
        self.select_wallet_in_list(row)

    def select_wallet_in_list(self, index: int):
        """选中钱包列表中的某项"""
        if self.model.rowCount():
            index %= self.model.rowCount()
            # 列表选中
            self.listViewWallets.setCurrentIndex(self.model.index(index))
            # 显示对应的控件
            self.stacked_layout.setCurrentIndex(index)

    def new_wallet_clicked(self):
        chain = select_chain(self)
        if chain:
            dialog = HdUi(mnemonic=mnemonic_from_entropy(), path=BIP44_DERIVATION_PATH, chain=chain, mode=Mode.Readonly)
            dialog.mnemonic_path_passphrase_set.connect(self.add_hd)
            dialog.exec()

    def import_wallet_clicked(self):
        _hd, _ = '助记词', '其它（扩展私钥）'
        selected, ok = QInputDialog.getItem(self, '钱包类型', '导入何种钱包？', [_hd, _], 0, False)
        if ok:
            if selected == _hd:
                chain = select_chain(self)
                if chain:
                    dialog = HdUi(chain=chain, mode=Mode.HD)
                    dialog.mnemonic_path_passphrase_set.connect(self.add_hd)
                    dialog.exec()
            elif selected == _:
                dialog = InputDialogUi(validator=AccountUi.wallet_import_input_valid)
                dialog.setWindowTitle('导入')
                dialog.setFixedWidth(950)
                dialog.labelDescription.setText(f'通过其它方式导入钱包。')
                dialog.text_entered.connect(self.import_wallet)
                dialog.exec()

    @classmethod
    def wallet_import_input_valid(cls, text) -> bool:
        return xprv_valid(text)

    def import_wallet(self, text: str):
        if text.startswith('xprv') or text.startswith('tprv'):
            self.add_hd({'xprv': text})

    def add_hd(self, hd: Dict):
        hd.update({'name': f'HD 钱包 {len(self.account) + 1}', 'receive_index': 0, 'receive_limit': 150, 'change_limit': 50, })
        self.add_wallet(hd)

    def add_wallet(self, wallet: Dict):
        self.account.append(wallet)
        write_account_file(self.account, self.account_file, self.password)
        self.refresh_wallet_list()
        self.add_wallet_widget(wallet, len(self.account) - 1)
        self.select_wallet_in_list(-1)

    def refresh_wallet_list(self):
        """刷新左侧的钱包列表"""
        self.model.update_fields(self.account)
        # noinspection PyUnresolvedReferences
        self.model.layoutChanged.emit()

    def add_wallet_widget(self, wallet: Dict, account_index: int):
        """在右侧新增控件"""
        w = WalletUi(self.app_settings, self.password, wallet, account_index)
        w.wallet_updated.connect(self.wallet_updated)
        w.network_status_updated.connect(self.network_status_updated)
        self.stacked_layout.addWidget(w)

    def wallet_updated(self, wallet: Dict, account_index: int):
        self.account[account_index] = wallet
        write_account_file(self.account, self.account_file, self.password)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        for i in range(self.stacked_layout.count()):
            self.stacked_layout.widget(i).close()
        super().closeEvent(a0)

    def wallet_list_context_menu(self, pos):
        menu = QMenu()
        action_rename = menu.addAction('重命名')
        action = menu.exec(self.listViewWallets.mapToGlobal(pos))
        if action == action_rename:
            self.context_menu_action_rename_clicked()

    def context_menu_action_rename_clicked(self):
        dialog = InputDialogUi()
        dialog.setWindowTitle('重命名')
        dialog.labelDescription.setText(f'输入新的钱包名称。')
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
