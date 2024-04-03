import json
import mimetypes
import os
import re
import sys
import uuid
from typing import Callable, Any
from typing import List, Dict

from PyQt6.QtCore import QFile, QByteArray, QIODevice, pyqtSlot, qInstallMessageHandler
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlSchemeHandler, QWebEngineUrlScheme
from PyQt6.QtWebEngineWidgets import QWebEngineView
from mvclib import Key
from mvclib.constants import Chain

basedir = os.path.abspath(os.path.dirname(sys.argv[0]))


class UrlSchemeHandler(QWebEngineUrlSchemeHandler):

    def requestStarted(self, job):
        url = job.requestUrl().toString()
        match_groups = re.match(r'^(local-file)://(.+(\..+))$', url)
        if match_groups:
            filename = match_groups.group(2)
            ext = match_groups.group(3)
            file = QFile(os.path.join(basedir, os.path.join('contract', filename)), job)
            file.open(QIODevice.OpenModeFlag.ReadOnly)
            job.reply(mimetypes.types_map[ext].encode('utf-8'), file)


# https://github.com/PyQt5/PyQt/tree/master/QWebEngineView
class ContractWebEngineView(QWebEngineView):
    def __init__(self):
        super(ContractWebEngineView, self).__init__()

        self.callbacks = {}

        scheme = QByteArray(b'local-file')
        QWebEngineUrlScheme.registerScheme(QWebEngineUrlScheme(scheme))
        profile = QWebEngineProfile.defaultProfile()
        profile.installUrlSchemeHandler(scheme, UrlSchemeHandler(self))
        self.setHtml(open(os.path.join(basedir, os.path.join('contract', 'index.html')), 'r', encoding='utf-8').read())

        channel = QWebChannel(self)
        channel.registerObject('Bridge', self)
        self.page().setWebChannel(channel)
        # https://stackoverflow.com/questions/58906917/warnings-when-instantiating-qwebchannel-object-in-javascript
        qInstallMessageHandler(lambda *args: None)

    @pyqtSlot(str)
    def js_callback(self, s: str):
        r = json.loads(s)
        if r['requestId'] in self.callbacks.keys():
            func = self.callbacks.pop(r['requestId'])
            func(r['result'])


class Contract:

    def __init__(self):
        self.engine = ContractWebEngineView()

    def register_callback(self, callback: Callable) -> str:
        request_id = str(uuid.uuid4())
        self.engine.callbacks[request_id] = callback
        return request_id

    def ft_transfer(self, ft: Dict, key: Key, receivers: List[Dict], callback: Callable[[Dict], Any]):
        request_id = self.register_callback(callback)
        params = {
            'requestId': request_id,
            'network': 'mainnet' if key.chain == Chain.MAIN else 'testnet',
            'purse': key.wif(),
            'feeb': 1,
            'codehash': ft['codeHash'],
            'genesis': ft['genesis'],
            'receivers': receivers,
            'senderWif': key.wif(),
            'utxoCount': ft['utxoCount'],
        }
        self.engine.page().runJavaScript(f'ftTransfer( {params})')
