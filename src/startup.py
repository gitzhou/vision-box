import json
import os
from contextlib import suppress
from pathlib import Path
from typing import List, Dict

from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox

from account import AccountUi
from base import require_password, activate
from designer.startup import Ui_formStartup
from set_password import SetPasswordUi
from utils import write_account_file, read_account_file

welcome = """Vision Box

https://visionbox.space

v0.1.0

- 接入测试网
- 导入或新建 HD 钱包，查看钱包地址库
- 收发 SPACE，支持从列表或地址库选择 UTXO，支持一转多
- 仅支持接收 FT"""


class StartupUi(QWidget, Ui_formStartup):
    app_settings_filename = os.path.join(str(Path.home()), '.vision-box.settings')

    def __init__(self):
        super(StartupUi, self).__init__()
        self.setupUi(self)

        self.account_file = ''
        self.account_window = None
        self.app_settings = {}

        self.setFixedSize(self.geometry().width(), self.geometry().height())
        self.pushButtonActivate.clicked.connect(lambda: activate(self.update_client_key))
        self.pushButtonNew.clicked.connect(self.new_account_button_clicked)
        self.pushButtonOpen.clicked.connect(self.open_account_button_clicked)

        self.plainTextEditWelcome.setPlainText(welcome)

        self.read_settings_file()

    def new_account_button_clicked(self):
        r = QFileDialog.getSaveFileName(parent=self, caption='新建账户', directory=str(Path.home()), filter='账户文件 (*.account)')
        self.account_file = r[0]
        if self.account_file:
            dialog = SetPasswordUi()
            dialog.password_set.connect(self.new_account_file)
            dialog.exec()

    def open_account_button_clicked(self):
        r = QFileDialog.getOpenFileName(parent=self, caption='打开账户', directory=str(Path.home()), filter='账户文件 (*.account)')
        self.account_file = r[0]
        if self.account_file:
            require_password(slot=self.open_account_file, account_name=Path(self.account_file).stem)

    def new_account_file(self, password: str):
        try:
            account = []
            write_account_file(account, self.account_file, password)
            self.show_account_window(account, password)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'账户“{Path(self.account_file).stem}”创建出错。\n\n{e}', QMessageBox.StandardButton.Ok)

    def open_account_file(self, password: str):
        try:
            self.show_account_window(read_account_file(self.account_file, password), password)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'账户“{Path(self.account_file).stem}”无法解锁，密码错误或文件损坏。\n\n{e}', QMessageBox.StandardButton.Ok)

    def show_account_window(self, account: List[Dict], password: str):
        self.account_window = AccountUi(self.app_settings, account, self.account_file, password)
        self.account_window.app_settings_updated.connect(self.app_settings_updated)
        self.account_window.show()
        self.close()

    def app_settings_updated(self, app_settings: Dict):
        self.app_settings = app_settings
        self.write_settings_file()

    def read_settings_file(self):
        with suppress(Exception):
            with open(StartupUi.app_settings_filename, 'r', encoding='utf-8') as f:
                self.app_settings = json.loads(f.read())
                return
        self.app_settings = {'client_key': '', }
        self.write_settings_file()

    def write_settings_file(self):
        with open(StartupUi.app_settings_filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.app_settings))

    def update_client_key(self, client_key: str):
        self.app_settings['client_key'] = client_key
        self.write_settings_file()


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = StartupUi()
    w.show()
    app.exec()
