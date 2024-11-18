import logging
from typing import Never

import requests

from .util import TokenProvider


class RestBaseRepository:
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        self.base_url = base_url
        self.token_provider = token_provider
        self.logger = logging.getLogger(self.__class__.__name__)

    def _headers(self) -> dict[str, str] | None:
        if self.token_provider is None:
            headers = None
        else:
            id_token = self.token_provider.get_token()
            headers = {'Authorization': f'Bearer {id_token}'}

        return headers

    def authenticated_get(self, url: str) -> requests.Response:
        return requests.get(url, timeout=2, headers=self._headers())

    def unexpected_error(self, resp: requests.Response) -> Never:
        resp.raise_for_status()

        raise requests.HTTPError('Unexpected response from server', response=resp)
