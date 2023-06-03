# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from pycxids.models.base_model import MyBaseModel

from pydantic import Field

# these are the not generated models, e.g. for storage

class TransferState(MyBaseModel):
    id: str,
    state: str,
    

