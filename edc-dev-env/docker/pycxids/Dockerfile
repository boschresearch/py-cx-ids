FROM python:3

WORKDIR /app

# install from git, because source is up in the hierarchy
# that can't be reached from within edc-dev-env
RUN pip install --no-cache-dir --upgrade git+https://github.com/boschresearch/py-cx-ids.git@dev
RUN pip install --no-cache-dir pytest

CMD []
