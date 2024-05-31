# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from pycxids.core.daps import Daps
from pycxids.iatp.iatp import Sts
from pycxids.miw.miw import Miw

class AuthFactory(ABC):
    """
    Use when it is not clear what implementation will be used to generate / fetch a token.
    An Interface.
    """
    @abstractmethod
    def get_token(self, aud: str, opts = {}):
        """
        aud: the audience for which the token is intended
        """
        pass

class MiwAuthFactory(AuthFactory, Miw):
    def __init__(self, miw_base_url: str, client_id: str = None, client_secret: str = None, token_url: str = None) -> None:
        #self.miw = Miw(base_url=miw_base_url, client_id=client_id, client_secret=client_secret, token_url=token_url)
        # could do explicit or python checks. explicit: super(Miw, self).__init__()
        super().__init__(base_url=miw_base_url, client_id=client_id, client_secret=client_secret, token_url=token_url)

    def get_token(self, aud: str, opts = {}):
        """
        Returns a JWT token
        """
        return self.get_vp(aud=aud)

class DapsAuthFactory(AuthFactory):
    """
    One implementation of an AuthFactory that fetches a auth token from a DAPS server
    """
    def __init__(self, daps_endpoint: str, private_key_fn: str, client_id: str, debug_messages = False, debug_out_dir: str = '') -> None:
        self.daps = Daps(daps_endpoint=daps_endpoint, private_key_fn=private_key_fn, client_id=client_id, debug_messages=debug_messages, debug_out_dir=debug_out_dir)

    def get_token(self, aud: str, opts = {}):
        """
        Returns a JWT token
        aud: the audience for which the token is intended
        """
        result = self.daps.get_daps_token(audience=aud)
        return result.get('access_token')

class IatpAuthFactory(AuthFactory):
    """
    Use the STS (Secure Token Service) to generate a token that we send over to the Provider.
    The Provider can use it to fetch the actual VPs from our CS (Credential Service).

    Since AuthFactory has a fixed get_token() with only the audience, we have to craete new instances for every provider_did.
    """
    def __init__(self, base_url: str, client_id: str, client_secret: str, token_url: str, our_did: str) -> None:
        """
        """
        self.sts = Sts(base_url=base_url, client_id=client_id, client_secret=client_secret, token_url=token_url, our_did=our_did)

        self.our_did = our_did

    def get_token(self, aud: str, opts = {}):
        """
        opts:
            bearer_scopes: []
        """
        bearer_scopes = opts.get('bearer_scopes', [Sts.MEMBERSHIP_CREDENTIAL]) # default is Membership only
        provider_did = opts.get('provider_did', self.our_did)
        bearer_scopes = opts.get('bearer_scopes', bearer_scopes)
        token = self.sts.get_sts_token(audience=aud, bearer_scopes=bearer_scopes, provider_did=provider_did)
        return token
