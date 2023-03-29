# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from typing import Union
import json
import os

class IdsBase():
    def __init__(self, debug_messages=False, debug_out_dir: str = '') -> None:
        self.debug_messages = debug_messages
        self.debug_out_dir = debug_out_dir

    def _debug_message(self, msg:Union[str, dict], fn:str):
        """
        For debugging of messages into a optionally given debug out dir.
        """
        if isinstance(msg, dict):
            msg = json.dumps(msg, indent=4)
        path_fn = os.path.join(self.debug_out_dir, fn)
        if not msg:
            msg = ''
        with(open(path_fn, 'w')) as f:
            f.write(msg)
