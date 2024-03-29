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
# build is only required once or after changes
./build.sh
# to rebuild from latest source use
./build.sh --no-cache
# or specify a dedicated service, e.g.
./build.sh --no-cache pycxids

# now start the infrastructure, e.g. a daps (mocked version of it) and the vault with the secrets
./start_infrastructure.sh
# wait a few seconds and run
./start_edc.sh
```

## Further configuration
Use a local `.env` file for e.g. the consumer HTTP endpoint if it is not the default (api-wrapper). Example:
```
EDC_RECEIVER_HTTP_ENDPOINT=http://dev:8000/datareference

```

# Azure Vault Help
Azure Vault is not used in this dev-env, because up until now, there is no way to mock it.
There is an upstream Issue to change this: https://github.com/eclipse-edc/Connector/issues/2686

In case Image and config is changed accordingly, some help to get key material into Azure Vault.
(It is important to know, that using the Azure portal did not work to get the keys in! Only the cli worked.)
```
az login
az keyvault secret set --name provider-key-1 --vault-name matthias-test-vault --file provider.key
az keyvault secret set --name provider-crt-1 --vault-name matthias-test-vault --file provider.crt
az keyvault secret set --name provider-ecryption-keys --vault-name matthias-test-vault --file provider-encryption.keys
az keyvault secret set --name provider-encryption-keys --vault-name matthias-test-vault --file provider-encryption.keys

```
