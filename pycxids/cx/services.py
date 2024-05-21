# Copyright (c) 2024 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from oauthlib.oauth2 import BackendApplicationClient
import requests
from requests_oauthlib import OAuth2Session

from pycxids.utils.api import GeneralApi


class BdrsDirectory(GeneralApi):
    """
    CX Specific service to map between BPN and DID

    Migration Guide: https://github.com/eclipse-tractusx/tractusx-edc/blob/main/docs/migration/Version_0.5.x_0.7.x.md#4-bpndid-resolution-service

    Github: https://github.com/eclipse-tractusx/bpn-did-resolution-service

    Swagger: https://eclipse-tractusx.github.io/bpn-did-resolution-service/openapi/directory-api/

    """
    BDRS_INT = "https://bpn-did-resolution-service.int.demo.catena-x.net/api/directory"

    def __init__(self, bdrs_base_url: str, membership_vp_jwt: str) -> None:
        headers = {
            "Authorization": f"Bearer {membership_vp_jwt}"
        }
        super().__init__(base_url=bdrs_base_url, headers=headers)

    def get_directory(self):
        j = self.get(path="/bpn-directory")
        return j


# EdcDiscovery in pycxids.portal.api instead
