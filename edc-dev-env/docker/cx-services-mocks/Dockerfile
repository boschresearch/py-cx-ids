# Copyright (c) 2024 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

FROM python:3

# install from git, because source is up in the hierarchy
# that can't be reached from within edc-dev-env
RUN pip install --no-cache-dir --upgrade git+https://github.com/boschresearch/py-cx-ids.git@dev

CMD ["python", "-m", "uvicorn", "pycxids.cx.mocks:app", "--host", "0.0.0.0", "--port", "8080"]
