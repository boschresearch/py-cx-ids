# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import FastAPI, Body, Request, HTTPException, status

from pycxids.core.http_binding.catalog import app as catalog
from pycxids.core.http_binding.negotiation_provider_api import app as negotiation_provider

app = FastAPI(title="IDS http binding", version='0.8')

app.include_router(catalog)
app.include_router(negotiation_provider)
