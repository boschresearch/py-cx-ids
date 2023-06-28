# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
import os
from fastapi import Request
from pycxids.core.http_binding.settings import settings

async def log_messages(request: Request, call_next):
    """
    TODO: before use: getting the content needs to feed in the content again.
    can be read only once
    """
    now = datetime.now()
    request_base_fn = f"{now}_request.json"
    response_base_fn = f"{now}_response.json"
    try:
        if not os.path.exists(settings.DEBUG_DIR):
            os.makedirs(settings.DEBUG_DIR)
    except:
        pass

    try:
        request_fn = os.path.join(settings.DEBUG_DIR, request_base_fn)
        with open(request_fn, 'wb') as f:
            f.write(request.body())
    except:
        pass

    # now the actual processing of the message
    response = await call_next(request)

    # and logging the response as well
    try:
        response_fn = os.path.join(settings.DEBUG_DIR, response_base_fn)
        with open(response_fn, 'wb') as f:
            f.write(response.body())
    except:
        pass

    return response


