from typing import Optional, List, Any, Dict

from PyQt6 import QtCore
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QInputDialog, QLineEdit, QApplication, QTableView, QHeaderView, QAbstractItemView, QMessageBox
from PyQt6.QtWidgets import QWidget
from mvclib import Unspent
from mvclib.constants import Chain

from input_dialog import InputDialogUi
from utils import format_coin


def require_password(slot, account_name: str = ''):
    dialog = InputDialogUi()
    dialog.setWindowTitle('输入密码')
    account_name = f' {account_name} ' if account_name else '文件'
    dialog.labelDescription.setText(f'账户{account_name}已加密，输入正确的密码解锁。')
    dialog.lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
    dialog.text_entered.connect(slot)
    dialog.exec()


def activate(slot):
    dialog = InputDialogUi()
    dialog.setWindowTitle('激活')
    dialog.labelDescription.setText(f'输入客户端密钥。')
    dialog.text_entered.connect(slot)
    dialog.exec()


def select_chain(parent: QWidget) -> Optional[Chain]:
    test_network, main_network = '测试网', '主网'
    selected, ok = QInputDialog.getItem(parent, "网络", "选择网络。", [test_network, main_network], 0, False)
    if ok:
        return Chain.TEST if selected == test_network else Chain.MAIN
    return None


def font(family: str, size: int) -> QFont:
    f = QFont()
    f.setFamily(family)
    f.setPointSize(size)
    return f


def copy_to_clipboard(text: str):
    QApplication.clipboard().setText(text)


def set_table_view(t: QTableView):
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    t.horizontalHeader().setSectionResizeMode(t.horizontalHeader().count() - 1, QHeaderView.ResizeMode.Stretch)
    t.verticalHeader().setVisible(False)
    t.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.horizontalHeader().setFont(font('Helvetica', 13))
    t.setSortingEnabled(True)


def still_under_development(parent: QWidget):
    QMessageBox.information(parent, '提示', '代码还在写。', QMessageBox.StandardButton.Ok)


class UnspentModel(QtCore.QAbstractTableModel):
    def __init__(self, unspents: Optional[List[Unspent]] = None):
        super(UnspentModel, self).__init__()
        self.unspents: List[Unspent] = []
        self._unspents: List[str] = []
        self.refresh(unspents)
        self.headers = ['高度', '输出', '地址', '数量']

    def refresh(self, unspents: Optional[List[Unspent]] = None):
        self.unspents = unspents or []
        self._unspents = [(str(u.height), f'{u.txid}:{u.vout}', u.address, format_coin(u.satoshi)) for u in self.unspents]
        # noinspection PyUnresolvedReferences
        self.layoutChanged.emit()

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._unspents[index.row()][index.column()]
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            return font('Monaco', 13)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._unspents)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.headers)

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole and orientation == QtCore.Qt.Orientation.Horizontal:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        self.unspents.sort(key=lambda x: UnspentModel.item_value(x, column), reverse=order == QtCore.Qt.SortOrder.DescendingOrder)
        self.refresh(self.unspents)

    @classmethod
    def item_value(cls, unspent: Unspent, column: int):
        return [unspent.height, f'{unspent.txid}:{unspent.vout}', unspent.address, unspent.satoshi][column]


class FtModel(QtCore.QAbstractTableModel):
    def __init__(self, fts: Optional[List[Dict]] = None):
        super(FtModel, self).__init__()
        self.fts: List[Dict] = []
        self._fts: List[str] = []
        self.refresh(fts)
        self.headers = ['符号', '名称', '标识', 'UTXO', '数量']

    def refresh(self, fts: Optional[List[Dict]] = None):
        self.fts = fts or []
        self._fts = []
        for i in range(len(self.fts)):
            ft = fts[i]
            token_id = f'{ft["codeHash"]}/{ft["genesis"]}'
            amount = format_coin(int(ft['confirmedString']) + int(ft['unconfirmedString']), ft['decimal'])
            self._fts.append((ft['symbol'], ft['name'], token_id, str(ft['utxoCount']), amount))
        # noinspection PyUnresolvedReferences
        self.layoutChanged.emit()

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._fts[index.row()][index.column()]
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            return font('Monaco', 13)

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._fts)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.headers)

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole and orientation == QtCore.Qt.Orientation.Horizontal:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        self.fts.sort(key=lambda x: FtModel.item_value(x, column), reverse=order == QtCore.Qt.SortOrder.DescendingOrder)
        self.refresh(self.fts)

    @classmethod
    def item_value(cls, ft: Dict, column: int):
        if column < 4:
            return [ft['symbol'], ft['name'], f'{ft["codeHash"]}/{ft["genesis"]}', ft['utxoCount']][column]
        return int(ft['confirmedString']) + int(ft['unconfirmedString'])


def copy_table_selected(t: QTableView, separator: str = ','):
    role = QtCore.Qt.ItemDataRole.DisplayRole
    rows = set(index.row() for index in t.selectedIndexes())
    lines = [separator.join([t.model().data(t.model().index(row, column), role) for column in range(t.model().columnCount())]) for row in rows]
    if lines:
        copy_to_clipboard('\n'.join(lines))
    t.setFocus()


def table_select_all(t: QTableView):
    t.selectAll()
    t.setFocus()
