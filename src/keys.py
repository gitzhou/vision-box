import random
from typing import List, Optional, Any, Union, Dict

from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QTableView
from mvclib import Unspent
from mvclib.hd import Xprv, Xpub, derive_xkeys_from_xkey

from base import font, set_table_view, copy_table_selected, table_select_all
from designer.keys import Ui_widgetKeys
from send_unspents import SendUnspentsUi
from utils import format_coin


class XkeyModel(QtCore.QAbstractTableModel):
    def __init__(self, xkeys: Optional[List[Union[Xpub, Xprv]]] = None, unspents: Optional[List[Unspent]] = None, change: int = 0):
        super(XkeyModel, self).__init__()
        self.change: int = change
        self.xkeys: List[Union[Xpub, Xprv]] = xkeys or []
        self.unspents: List[Unspent] = []
        self._xkeys: List[str] = []
        self.refresh(unspents)
        self.headers = ['路径', '公钥', '地址', 'UTXO', '余额']

    def refresh(self, unspents: Optional[List[Unspent]] = None):
        self.unspents = unspents or []
        self._xkeys = []
        for i in range(len(self.xkeys)):
            path = f'{self.change}/{str(i).zfill(len(str(len(self.xkeys))))}'
            balance = sum([unspent.satoshi if unspent.address == self.xkeys[i].address() else 0 for unspent in self.unspents])
            utxo = sum([1 if unspent.address == self.xkeys[i].address() else 0 for unspent in self.unspents])
            self._xkeys.append((path, self.xkeys[i].public_key().hex(), self.xkeys[i].address(), str(utxo), format_coin(balance)))
        # noinspection PyUnresolvedReferences
        self.layoutChanged.emit()

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._xkeys[index.row()][index.column()]
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            return font('Monaco', 13)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._xkeys)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.headers)

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole and orientation == QtCore.Qt.Orientation.Horizontal:
            return self.headers[section]
        return super().headerData(section, orientation, role)


class KeysUi(QWidget, Ui_widgetKeys):
    request_refresh = QtCore.pyqtSignal()

    def __init__(self, password: str, w: Dict, unspents: Optional[List[Unspent]] = None):
        super(KeysUi, self).__init__()
        self.setupUi(self)

        self.password = password
        xprv = w.get('xprv')
        if xprv:
            self.xkey: Union[Xpub, Xprv] = Xprv(xprv)
        else:
            self.xkey: Union[Xpub, Xprv] = Xpub(w['xpub'])
        self.chain = self.xkey.chain

        self.receive_xkeys: List[Union[Xpub, Xprv]] = derive_xkeys_from_xkey(self.xkey, 0, w['receive_limit'], 0)
        self.change_xkeys: List[Union[Xpub, Xprv]] = derive_xkeys_from_xkey(self.xkey, 0, w['change_limit'], 1)
        self.unspents: List[Unspent] = unspents or []
        self.send_unspents_dialog = None

        self.receive_model = XkeyModel(self.receive_xkeys, self.unspents, 0)
        self.receive_proxy_model = QtCore.QSortFilterProxyModel()
        self.receive_proxy_model.setSourceModel(self.receive_model)
        self.receive_proxy_model.setFilterKeyColumn(2)
        self.tableViewReceive.setModel(self.receive_proxy_model)
        set_table_view(self.tableViewReceive)
        self.tableViewReceive.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)

        self.change_model = XkeyModel(self.change_xkeys, self.unspents, 1)
        self.change_proxy_model = QtCore.QSortFilterProxyModel()
        self.change_proxy_model.setSourceModel(self.change_model)
        self.change_proxy_model.setFilterKeyColumn(2)
        self.tableViewChange.setModel(self.change_proxy_model)
        set_table_view(self.tableViewChange)
        self.tableViewChange.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)

        self.lineEditReceiveSearch.textChanged.connect(self.receive_proxy_model.setFilterFixedString)
        self.lineEditChangeSearch.textChanged.connect(self.change_proxy_model.setFilterFixedString)

        self.setWindowTitle(f'地址库 | {w["name"]}')
        self.tabWidgetKeys.setCurrentIndex(0)

        self.tableViewReceive.selectionModel().selectionChanged.connect(lambda: self.enable_receive_send_button())
        self.pushButtonReceiveSend.setEnabled(False)
        self.pushButtonReceiveSend.clicked.connect(lambda: self.send_button_clicked(self.tableViewReceive))
        self.pushButtonReceiveClearSelection.clicked.connect(self.tableViewReceive.clearSelection)
        self.pushButtonReceiveCopy.clicked.connect(lambda: copy_table_selected(self.tableViewReceive))
        self.pushButtonReceiveSelectAll.clicked.connect(lambda: table_select_all(self.tableViewReceive))

        self.tableViewChange.selectionModel().selectionChanged.connect(lambda: self.enable_change_send_button())
        self.pushButtonChangeSend.setEnabled(False)
        self.pushButtonChangeSend.clicked.connect(lambda: self.send_button_clicked(self.tableViewChange))
        self.pushButtonChangeClearSelection.clicked.connect(self.tableViewChange.clearSelection)
        self.pushButtonChangeCopy.clicked.connect(lambda: copy_table_selected(self.tableViewChange))
        self.pushButtonChangeSelectAll.clicked.connect(lambda: table_select_all(self.tableViewChange))

    def enable_receive_send_button(self):
        self.pushButtonReceiveSend.setEnabled(len(self.unspents_selected(self.tableViewReceive)) > 0 and type(self.xkey) is Xprv)

    def enable_change_send_button(self):
        self.pushButtonChangeSend.setEnabled(len(self.unspents_selected(self.tableViewChange)) > 0 and type(self.xkey) is Xprv)

    def refresh(self, password: Optional[str] = None, w: Optional[Dict] = None, unspents: Optional[List[Unspent]] = None):
        if password is not None:
            self.password = password
        if w is not None:
            self.setWindowTitle(f'地址库 | {w["name"]}')
        if unspents is not None:
            self.unspents = unspents
            self.receive_proxy_model.beginResetModel()
            self.receive_model.refresh(self.unspents)
            self.receive_proxy_model.endResetModel()
            self.tableViewReceive.clearSelection()
            self.change_proxy_model.beginResetModel()
            self.change_model.refresh(self.unspents)
            self.change_proxy_model.endResetModel()
            self.tableViewChange.clearSelection()

    def unspents_selected(self, t: QTableView) -> List[Unspent]:
        rows = list(set(index.row() for index in t.selectionModel().selection().indexes()))
        addresses = [t.model().index(row, 2).data() for row in rows]
        unspents: List[Unspent] = []
        for unspent in self.unspents:
            if unspent.address in addresses:
                unspents.append(unspent)
        return unspents

    def send_button_clicked(self, t: QTableView):
        selected_unspents = self.unspents_selected(t)
        change_address = random.choice(self.change_xkeys).address()
        self.send_unspents_dialog = SendUnspentsUi(self.password, selected_unspents, self.chain, change_address, True)
        if self.send_unspents_dialog.exec():
            t.clearSelection()
            self.request_refresh.emit()
