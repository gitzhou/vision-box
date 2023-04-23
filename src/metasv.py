from typing import Dict, List

import requests
from mvclib.service import MvcApi
from mvclib.utils import decode_address

TIMEOUT = 3


def ft_balance(address: str, client_key: str = '', **kwargs) -> List[Dict]:
    try:
        _, chain = decode_address(address)
        p = MvcApi(chain=chain, client_key=client_key)
        path = f'/contract/ft/address/{address}/balance'
        _r = requests.get(f'{p.url}{path}', headers=p.parse_headers(path), timeout=TIMEOUT)
        _r.raise_for_status()
        return _r.json()
    except Exception as e:
        if kwargs.get('throw'):
            raise e
    return []
