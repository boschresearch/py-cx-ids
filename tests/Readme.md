# Intro
Tests need a EDC environment, e.g. local `edc-dev-env` setup

It is recommended to setup `Visual Studio Code Development Container`

Configure `.devcontainer/devcontainer.json` with `"runArgs": ["--network", "edc-dev-env_default", "--hostname", "dev" ]`
This will connect to the environment started inside `edc-dev-env` directory.


# Tests
`tests` create assets (and friends) with the `provider` instance and fetch it via the `consumer` instance. Currently, including the `api-wrapper` and of course the `daps` (mocked daps) in the background. All this with the official `product-edc` images.

## Test execution
```
# prepare virtual env if required
#python3 -m venv venv
#source ./venv/bin/activate

# install all dependencies
pip install -r ./daps-mock/requirements.txt
# run the actual test - make sure, the EDC instances are running...
python ./tests/test_assets.py
```
