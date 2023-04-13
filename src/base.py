from typing import Optional, List, Any, Dict, Callable

from PyQt6 import QtCore, QtGui
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QInputDialog, QLineEdit, QApplication, QTableView, QHeaderView, QAbstractItemView, QMessageBox
from PyQt6.QtWidgets import QWidget
from mvclib import Unspent
from mvclib.constants import Chain

from input_dialog import InputDialogUi
from set_password import SetPasswordUi
from utils import format_coin


def require_password(_parent: QWidget, _callback: Callable, _password: Optional[str] = None, **kwargs):
    dialog = InputDialogUi()
    dialog.setWindowTitle('Password')
    dialog.labelDescription.setText('The account file is encrypted, enter the correct password to unlock it.')
    dialog.lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
    dialog.lineEdit.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression("[\x21-\x7E]*"), None))
    dialog.text_entered.connect(lambda text: _require_password(_parent, _callback, text, _password, **kwargs))
    dialog.exec()


def _require_password(_parent: QWidget, _callback: Callable, _text: str, _password: Optional[str] = None, **kwargs):
    if _password is None:
        _callback(**{**kwargs, 'password': _text})
    elif _text == _password:
        _callback(**kwargs)
    else:
        QMessageBox.critical(_parent, 'Critical', 'The account password you entered is not correct.', QMessageBox.StandardButton.Ok)


def set_password(slot: Callable):
    dialog = SetPasswordUi()
    dialog.password_set.connect(slot)
    dialog.exec()


def activate(slot: Callable):
    dialog = InputDialogUi()
    dialog.setWindowTitle('Activate')
    dialog.labelDescription.setText('Enter a client secret to activate this application.')
    dialog.text_entered.connect(slot)
    dialog.exec()


def select_chain(parent: QWidget) -> Optional[Chain]:
    main_network = 'Mainnet'
    test_network = 'Testnet'
    selected, ok = QInputDialog.getItem(parent, "Network", "Select a network.", [main_network, test_network], 0, False)
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


class UnspentModel(QtCore.QAbstractTableModel):
    def __init__(self, unspents: Optional[List[Unspent]] = None):
        super(UnspentModel, self).__init__()
        self.unspents: List[Unspent] = []
        self._unspents: List[str] = []
        self.update_fields(unspents)
        self.headers = ['Height', 'Outpoint', 'Address', 'Amount']

    def update_fields(self, unspents: Optional[List[Unspent]] = None):
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
        self.update_fields(self.unspents)

    @classmethod
    def item_value(cls, unspent: Unspent, column: int):
        return [unspent.height, f'{unspent.txid}:{unspent.vout}', unspent.address, unspent.satoshi][column]


class FtModel(QtCore.QAbstractTableModel):
    def __init__(self, fts: Optional[List[Dict]] = None):
        super(FtModel, self).__init__()
        self.fts: List[Dict] = []
        self._fts: List[str] = []
        self.update_fields(fts)
        self.headers = ['Symbol', 'Name', 'Identifier', 'UTXO', 'Amount']

    def update_fields(self, fts: Optional[List[Dict]] = None):
        self.fts = fts or []
        self._fts = []
        for i in range(len(self.fts)):
            ft = fts[i]
            token_id = f'{ft["codeHash"]}/{ft["genesis"]}'
            amount = int(ft['confirmedString']) + int(ft['unconfirmedString'])
            self._fts.append((ft['symbol'], ft['name'], token_id, str(ft['utxoCount']), format_coin(amount, ft['decimal'])))
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
        self.update_fields(self.fts)

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
