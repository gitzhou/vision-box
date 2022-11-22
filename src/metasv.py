from typing import Dict, List

import requests
from mvclib.constants import Chain
from mvclib.service import MetaSV

TIMEOUT = 3


def ft_balance(address: str, chain: Chain, client_key: str = '', **kwargs) -> List[Dict]:
    try:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', }
        p = MetaSV(chain=chain, headers=headers, timeout=TIMEOUT, client_key=client_key)
        path = f'/contract/ft/address/{address}/balance'
        _r = requests.get(f'{p.url}{path}', headers=p.parse_headers(path), timeout=p.timeout)
        _r.raise_for_status()
        return _r.json()
    except Exception as e:
        if kwargs.get('throw'):
            raise e
    return []
