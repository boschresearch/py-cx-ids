# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from pycxids.core.daps import Daps
from pycxids.miw.miw import Miw

class AuthFactory(ABC):
    """
    Use when it is not clear what implementation will be used to generate / fetch a token.
    An Interface.
    """
    @abstractmethod
    def get_token(self, aud: str):
        """
        aud: the audience for which the token is intended
        """
        pass

class MiwAuthFactory(AuthFactory):
    def __init__(self, miw_base_url: str, client_id: str = None, client_secret: str = None, token_url: str = None) -> None:
        self.miw = Miw(base_url=miw_base_url, client_id=client_id, client_secret=client_secret, token_url=token_url)

    def get_token(self, aud: str):
        """
        Returns a JWT token
        """
        return self.miw.get_vp(aud=aud)

class DapsAuthFactory(AuthFactory):
    """
    One implementation of an AuthFactory that fetches a auth token from a DAPS server
    """
    def __init__(self, daps_endpoint: str, private_key_fn: str, client_id: str, debug_messages = False, debug_out_dir: str = '') -> None:
        self.daps = Daps(daps_endpoint=daps_endpoint, private_key_fn=private_key_fn, client_id=client_id, debug_messages=debug_messages, debug_out_dir=debug_out_dir)

    def get_token(self, aud: str):
        """
        Returns a JWT token
        aud: the audience for which the token is intended
        """
        result = self.daps.get_daps_token(audience=aud)
        return result.get('access_token')
