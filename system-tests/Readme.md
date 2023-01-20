# Intro
Tests need a EDC environment, e.g. local `edc-dev-env` setup

It is recommended to setup `Visual Studio Code Development Container`

Configure `.devcontainer/devcontainer.json` with `"runArgs": ["--network", "edc-dev-env_default", "--hostname", "dev" ]`
This will connect to the environment started inside `edc-dev-env` directory.

