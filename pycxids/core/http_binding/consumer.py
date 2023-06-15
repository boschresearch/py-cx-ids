# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import FastAPI, Body, Request, HTTPException, status

from pycxids.core.http_binding.settings import CONSUMER_DISABLE_RECEIVER_API
from pycxids.core.http_binding.negotiation_consumer_api import app as negotiation_consumer
from pycxids.core.http_binding.transfer_consumer_api import app as transfer_consumer
from pycxids.core.http_binding.consumer_receiver_api import app as receiver_api

app = FastAPI(title="IDS http binding - Consumer", version='0.8')

app.include_router(negotiation_consumer)
app.include_router(transfer_consumer)


if not CONSUMER_DISABLE_RECEIVER_API:
    app.include_router(receiver_api)
