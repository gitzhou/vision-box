import json
import os
from contextlib import suppress
from pathlib import Path
from typing import List, Dict

from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox

from account import AccountUi
from base import require_password, activate, set_password
from designer.startup import Ui_formStartup
from utils import write_account_file, read_account_file

welcome = """
                                                         USE AT YOUR OWN RISK

                                                           https://visionbox.space

            1FY3movXuCtFiFMYQMZFBAtmtm2oBX3yzC  # feel free to buy me a coffee :)


v0.3.2
------

- Dependencies upgrade


v0.3.1
------

- Bug fix and dependencies upgrade


v0.3.0
------

- Support Mainnet
- Support sending FT
- Fix known issues, optimization, and code refactoring


v0.2.0
------

- Support changing the account password
- Support wallet renaming and information viewing
- Support for importing wallets through other ways
- Support for watching-only wallets
- Support viewing the private key of each address in the wallet keys
- Fix known issues, optimization, and code refactoring


v0.1.0
------

- Access to Testnet
- Import or create a new HD wallet, and view keys in the wallet
- Send and receive SPACE, support selecting UTXO and pay-to-many
- only supports receive FT"""


class StartupUi(QWidget, Ui_formStartup):
    app_settings_filename = os.path.join(str(Path.home()), '.vision-box.settings')

    def __init__(self):
        super(StartupUi, self).__init__()
        self.setupUi(self)

        self.account_file = ''
        self.account_window = None
        self.app_settings = {}

        self.setFixedSize(600, 680)
        self.setWindowTitle('Vision Box')
        self.plainTextEditWelcome.setPlainText(welcome)
        self.pushButtonActivate.clicked.connect(lambda: activate(self.update_client_key))
        self.pushButtonNew.clicked.connect(self.new_account_button_clicked)
        self.pushButtonOpen.clicked.connect(self.open_account_button_clicked)

        self.read_settings_file()

    def new_account_button_clicked(self):
        r = QFileDialog.getSaveFileName(parent=self, caption='Create Account', directory=str(Path.home()), filter='Account file (*.account)')
        self.account_file = r[0]
        if self.account_file:
            set_password(self.new_account_file)

    def open_account_button_clicked(self):
        r = QFileDialog.getOpenFileName(parent=self, caption='Open Account', directory=str(Path.home()), filter='Account file (*.account)')
        self.account_file = r[0]
        if self.account_file:
            require_password(self, self.open_account_file)

    def new_account_file(self, password: str):
        try:
            account = []
            write_account_file(account, self.account_file, password)
            self.show_account_window(account, password)
        except Exception as e:
            QMessageBox.critical(self, 'Critical', f'Error creating account "{Path(self.account_file).stem}".\n\n{e}', QMessageBox.StandardButton.Ok)

    def open_account_file(self, password: str):
        try:
            self.show_account_window(read_account_file(self.account_file, password), password)
        except Exception as e:
            message = f'The account "{Path(self.account_file).stem}" cannot be unlocked, the password is wrong or the file is damaged.\n\n{e}'
            QMessageBox.critical(self, 'Critical', message, QMessageBox.StandardButton.Ok)

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
