import hashlib
import json
from contextlib import suppress
from typing import Dict, List, Optional

from mvclib import PublicKey
from mvclib.aes import aes_encrypt_with_iv, aes_decrypt_with_iv
from mvclib.constants import Chain
from mvclib.hd import Xprv, Xpub
from mvclib.utils import decode_wif, decode_address

COIN_DECIMAL = 8


def sha256(payload: bytes) -> bytes:
    return hashlib.sha256(payload).digest()


def encrypt_account(account: List[Dict], password: str) -> bytes:
    k: bytes = sha256(password.encode('utf-8'))
    key, iv = k[:16], k[16:]
    message: bytes = json.dumps(account).encode('utf-8')
    return aes_encrypt_with_iv(key, iv, message)


def decrypt_account(message: bytes, password: str) -> List[Dict]:
    k: bytes = sha256(password.encode('utf-8'))
    key, iv = k[:16], k[16:]
    account: str = aes_decrypt_with_iv(key, iv, message).decode('utf-8')
    return json.loads(account)


def write_account_file(account: List[Dict], file: str, password: str):
    with open(file, 'wb') as f:
        f.write(encrypt_account(account, password))


def read_account_file(file: str, password: str) -> List[Dict]:
    with open(file, 'rb') as f:
        return decrypt_account(f.read(), password)


def format_coin(amount: int, decimal: int = 8, decimal_digits: int = None, fixed_length: int = 0, rstrip: bool = False) -> str:
    decimal_digits = decimal_digits or decimal
    s = format(float(amount) / 10 ** decimal, f'.{decimal_digits}f')
    if fixed_length:
        s = s[0:fixed_length]
    if rstrip and '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


def xprv_valid(xprv: str, chain: Optional[Chain] = None) -> bool:
    with suppress(Exception):
        _xprv = Xprv(xprv)
        if chain:
            assert _xprv.chain == chain
        return True
    return False


def xpub_valid(xpub: str, chain: Optional[Chain] = None) -> bool:
    with suppress(Exception):
        _xpub = Xpub(xpub)
        if chain:
            assert _xpub.chain == chain
        return True
    return False


def wif_valid(wif: str, compressed: Optional[bool] = None, chain: Optional[Chain] = None) -> bool:
    with suppress(Exception):
        _, _compressed, _chain = decode_wif(wif)
        if compressed is not None:
            assert _compressed == compressed
        if chain:
            assert _chain == chain
        return True
    return False


def address_valid(address: str, chain: Optional[Chain] = None) -> bool:
    with suppress(Exception):
        _, _chain = decode_address(address)
        if chain:
            assert _chain == chain
        return True
    return False


def pk_valid(pk: str) -> bool:
    with suppress(Exception):
        PublicKey(pk)
        return True
    return False
