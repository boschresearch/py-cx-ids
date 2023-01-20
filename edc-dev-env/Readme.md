# Warning
**WARNING: DO NEVER RUN THIS IN A PUBLIC NETWORK**

This is for pure development purposes and it's NOT secure in any way to run in public networks. Only use this on local development machines.

# Introduction

This is a development environment for Catena-X `product-edc` which is the Catena-X version of the upstream EDC repository.

It is customized for the Catena-X needs. The official `product-edc` images do need special environment, e.g. postrgres and either Azure Vault or Hashicopr Vault. Filesystem Vault for example, is not supported.

Also the images require a running DAPS instance.

For local testing, this is a challenge. Therefore, this repository to provide a way to use official images (no need to rebuild from sources), but open up to setup your own EDC instances with development keys and no need to use the official, central DAPS instance.

# Keys
The keys are generated with `./bin/generate_keys.sh` but default development keys are provided as part of the repository. If you change the keys, beware, that some configs (`control-plane.properties`) need to be updated.

# Getting started
Currently, the infrastructure (vault and postgres) need to be started separately with:
```
docker-compose -f docker-compose-infrastructure.yaml up --force-recreate

docker-compose -f docker-compose.yaml -f docker-compose-api-wrapper.yaml up --force-recreate

```
Consider using `-V, --renew-anon-volumes` or `docker-compose volumes --down` (using `-f ...` for the individual docker-compose files)

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

# Dev Notes
`pip install pyjwt[crypto]` required for RSA.

